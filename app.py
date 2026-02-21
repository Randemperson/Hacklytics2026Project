"""
Real Estate AI — Flask Web Application
Provides a voice-enabled chat interface for finding affordable housing.
"""
import logging
import os

from flask import Flask, jsonify, render_template, request

from src.housing_ai import HousingAI
from src.agent_caller import AgentCaller
from src.chatbot import Chatbot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-housing-ai")

# Initialise shared components once at startup
_ai = HousingAI()
_caller = AgentCaller()
_chatbot = Chatbot(housing_ai=_ai, agent_caller=_caller, voice_enabled=False)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    cities = _ai.get_cities()
    languages = _ai.get_languages()
    min_rent, max_rent = _ai.get_price_range()
    return render_template(
        "index.html",
        cities=cities,
        languages=languages,
        min_rent=int(min_rent),
        max_rent=int(max_rent),
    )


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():
    """Process a text (or transcribed voice) query and return a reply."""
    data = request.get_json(force=True, silent=True) or {}
    user_input = (data.get("message") or "").strip()
    if not user_input:
        return jsonify({"error": "No message provided."}), 400

    reply = _chatbot.process_turn(user_input)

    # Serialise the last result set so the UI can render listing cards
    listings = []
    if _chatbot._last_results is not None and not _chatbot._last_results.empty:
        listings = _chatbot._last_results.fillna("").to_dict(orient="records")

    return jsonify({"reply": reply, "listings": listings})


@app.route("/api/search", methods=["GET"])
def search():
    """Structured search endpoint — accepts query parameters directly."""
    params: dict = {}

    max_rent = request.args.get("max_rent")
    if max_rent:
        params["max_rent"] = float(max_rent)

    min_bedrooms = request.args.get("min_bedrooms")
    if min_bedrooms:
        params["min_bedrooms"] = int(min_bedrooms)

    city = request.args.get("city")
    if city:
        params["city"] = city

    state = request.args.get("state")
    if state:
        params["state"] = state

    language = request.args.get("language")
    if language:
        params["language"] = language

    for flag in ("section8", "hud_approved", "low_income_only",
                 "needs_transit", "pets_allowed", "accessibility"):
        val = request.args.get(flag, "").lower()
        if val in ("true", "1", "yes"):
            params[flag] = True

    top_n = int(request.args.get("top_n", 10))
    params["top_n"] = top_n

    results = _ai.search(**params)
    listings = results.fillna("").to_dict(orient="records") if not results.empty else []
    return jsonify({"count": len(listings), "listings": listings})


@app.route("/api/contact", methods=["POST"])
def contact():
    """Contact an agent about a specific listing."""
    data = request.get_json(force=True, silent=True) or {}

    required = {"listing_id", "user_name", "user_phone"}
    missing = required - set(data.keys())
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    listing_id = int(data["listing_id"])
    row = _ai.df[_ai.df["id"] == listing_id]
    if row.empty:
        return jsonify({"error": f"Listing {listing_id} not found."}), 404

    listing = row.iloc[0].fillna("").to_dict()
    result = _caller.contact_agent_for_listing(
        listing=listing,
        user_name=data["user_name"],
        user_phone=data["user_phone"],
        user_email=data.get("user_email", ""),
        preferred_language=data.get("language", "English"),
        method=data.get("method", "email"),
    )
    return jsonify(result)


@app.route("/api/listings/<int:listing_id>")
def get_listing(listing_id: int):
    """Return full details for a single listing."""
    row = _ai.df[_ai.df["id"] == listing_id]
    if row.empty:
        return jsonify({"error": "Listing not found."}), 404
    return jsonify(row.iloc[0].fillna("").to_dict())


@app.route("/api/meta")
def meta():
    """Return metadata about available filter options."""
    min_rent, max_rent = _ai.get_price_range()
    return jsonify({
        "cities": _ai.get_cities(),
        "languages": _ai.get_languages(),
        "min_rent": min_rent,
        "max_rent": max_rent,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting Real Estate AI on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=debug)
