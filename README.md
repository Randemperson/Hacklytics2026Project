# 🏠 Real Estate AI — Affordable Housing Assistant

A voice-enabled AI assistant that helps **immigrants and minorities** find low-cost housing and connect with real estate agents.

![Real Estate AI UI](https://github.com/user-attachments/assets/0ce2927c-f60d-46dc-b18b-944401850633)

---

## Features

| Feature | Description |
|---|---|
| 🔍 **AI Housing Search** | Natural-language queries ranked by affordability score |
| 🎤 **Voice Activation** | Speak your search — Web Speech API in the browser; `SpeechRecognition` + `pyttsx3`/`gTTS` in CLI |
| 🌍 **Multilingual Support** | Filter listings by agent language (Spanish, Chinese, Amharic, Arabic, French, Somali, Vietnamese, Hindi, and more) |
| 📋 **Smart Filters** | Section 8, HUD approved, low-income eligible, near transit, pets, accessibility |
| 📞 **Agent Contact** | Contact agents via email, SMS, or automated phone call (Twilio) — in the user's preferred language |
| 🌐 **Web UI** | Responsive chat + filter panel with live listing cards |
| 💻 **CLI Mode** | Terminal chatbot with optional microphone input |

---

## Project Structure

```
├── app.py                  # Flask web application & REST API
├── requirements.txt
├── data/
│   └── housing_data.csv    # Affordable housing dataset (30 listings, ATL metro)
├── src/
│   ├── housing_ai.py       # AI recommendation engine (search, scoring, NLP parsing)
│   ├── voice_interface.py  # Speech-to-text & text-to-speech wrapper
│   ├── agent_caller.py     # Agent contact via Twilio phone/SMS or SMTP email
│   └── chatbot.py          # Conversational controller (web & CLI)
├── templates/
│   └── index.html          # Voice-enabled chat + filter UI
├── static/
│   ├── css/style.css
│   └── js/app.js           # Web Speech API, chat bubbles, listing cards
└── tests/
    └── test_housing_ai.py  # 41 unit tests
```

---

## Quick Start

**Prerequisites:** Python 3.9 or later, `pip`, and `git`.

### 1. Clone the repository

```bash
git clone https://github.com/Randemperson/Hacklytics2026Project.git
cd Hacklytics2026Project
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Tip:** use a virtual environment to keep packages isolated:
> ```bash
> python -m venv .venv
> source .venv/bin/activate   # macOS / Linux
> .venv\Scripts\activate      # Windows
> pip install -r requirements.txt
> ```

### 3. Run the web app

```bash
python app.py
```

Then open **http://localhost:5000** in your browser. You should see the chat
panel on the left and the filter panel on the right. Type (or click the 🎤
button) to ask for housing, for example:

> *"2 bedroom apartment under $800 in Atlanta with Spanish-speaking agent"*

Matching listings will appear below as cards with agent contact details.

### 4. Run the CLI chatbot (no browser needed)

```bash
python -c "from src.chatbot import Chatbot; Chatbot().run_cli()"
```

Type queries at the `You:` prompt. Type `quit` to exit.

### 5. Enable voice in CLI (optional)

```bash
# Install audio packages first
pip install SpeechRecognition pyttsx3

python -c "from src.chatbot import Chatbot; Chatbot(voice_enabled=True).run_cli()"
```

The assistant will listen on your default microphone and speak results aloud.

### 6. Run the tests

```bash
pytest tests/ -v
```

All 41 tests should pass with no configuration required.

---

## Example Queries

- *"Find 2-bedroom apartments under \$800 in Atlanta"*
- *"Show Section 8 housing with Spanish-speaking agents"*
- *"Wheelchair accessible housing near public transit"*
- *"Affordable 1-bedroom for family, Somali-speaking agent"*
- *"HUD approved housing in Decatur under \$750"*

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI |
| `POST` | `/api/chat` | Natural-language chat (`{"message": "..."}`) |
| `GET` | `/api/search` | Structured search with query params |
| `POST` | `/api/contact` | Contact an agent for a listing |
| `GET` | `/api/listings/<id>` | Get a single listing |
| `GET` | `/api/meta` | Available cities, languages, price range |

### Search parameters (`/api/search`)

`max_rent`, `min_bedrooms`, `city`, `state`, `language`, `section8`, `hud_approved`, `low_income_only`, `needs_transit`, `pets_allowed`, `accessibility`, `top_n`

---

## Agent Contact (Twilio + Email)

Set environment variables to enable automated contact:

```bash
# Phone / SMS (Twilio)
export TWILIO_ACCOUNT_SID=ACxxxxxxxx
export TWILIO_AUTH_TOKEN=xxxxxxxx
export TWILIO_PHONE_NUMBER=+15550001234

# Email (Gmail / SMTP)
export SMTP_HOST=smtp.gmail.com
export SMTP_USER=you@gmail.com
export SMTP_PASSWORD=your-app-password
```

Without credentials, the system still shows the agent's direct phone and email on each listing card.

---

## About the Housing Data

### Where does the data come from?

`data/housing_data.csv` is **synthetic** — the listings, agent names, phone
numbers, and email addresses are **fictitious** and were hand-crafted for this
project. They were designed to reflect realistic patterns for affordable
housing in the **Atlanta, GA metro area** (rent levels, neighborhood names,
ZIP codes, transit access) based on publicly available information about the
region, but **no real rental listings or real people are represented**.

The phone numbers all use the `555` exchange (a standard placeholder for
fictional US numbers), and the email addresses point to non-existent domains.

### Why synthetic data?

Real affordable-housing databases require licensing agreements or API keys and
may contain personally identifiable information. Synthetic data lets the
project demonstrate all AI and voice features without those dependencies, and
without exposing anyone's private information.

### Dataset schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Unique listing identifier |
| `address` | string | Street address |
| `city` | string | City name |
| `state` | string | Two-letter state code (all `GA`) |
| `zip_code` | int | US ZIP code |
| `monthly_rent` | int | Monthly rent in USD |
| `bedrooms` | int | Number of bedrooms |
| `bathrooms` | float | Number of bathrooms |
| `sqft` | int | Approximate square footage |
| `property_type` | string | `Apartment`, `House`, `Townhouse`, … |
| `nearby_transit` | bool | `Yes` / `No` — whether public transit is nearby |
| `languages_spoken` | string | Comma-separated list of languages the agent speaks |
| `agent_name` | string | Listing agent's full name |
| `agent_phone` | string | Agent phone number (fictitious `555` numbers) |
| `agent_email` | string | Agent email address (fictitious domains) |
| `section8_accepted` | bool | Whether the landlord accepts Section 8 vouchers |
| `hud_approved` | bool | Whether the property is HUD-approved |
| `low_income_eligible` | bool | Whether the unit qualifies for low-income programs |
| `income_limit_percent_ami` | int | Maximum qualifying household income as % of Area Median Income |
| `utilities_included` | string | Which utilities are included (e.g. `Water/Trash`), or `None` |
| `pets_allowed` | bool | Whether pets are allowed |
| `accessibility_features` | string | Accessibility features (e.g. `Wheelchair ramp`, `Elevator`), or `None` |
| `neighborhood_description` | string | Short free-text description |
| `latitude` | float | Approximate latitude |
| `longitude` | float | Approximate longitude |

### How to use real data

To replace the synthetic listings with real ones, swap out
`data/housing_data.csv` with a file that uses the same column headers.
Useful public sources include:

| Source | URL | What it contains |
|--------|-----|-----------------|
| **HUD Fair Market Rents** | https://www.huduser.gov/portal/datasets/fmr.html | Official FMR data by metro/county |
| **HUD LIHTC Database** | https://lihtc.huduser.gov | Low-Income Housing Tax Credit properties nationwide |
| **Atlanta Housing Authority** | https://atlantahousing.org | Public housing and voucher programs |
| **Georgia DCA Housing Search** | https://www.dca.ga.gov/safe-affordable-housing | State-level affordable housing locator |
| **HUD's Affordable Apartment Search** | https://www.hud.gov/topics/rental_assistance | HUD-assisted rental search |
| **OpenStreetMap / Overpass API** | https://overpass-api.de | Geocoding and neighborhood data |
| **Zillow Research Data** | https://www.zillow.com/research/data | Public rental-price datasets (CSV) |

See [`data/DATA_SOURCES.md`](data/DATA_SOURCES.md) for detailed guidance on
ingesting real data into this project.

The AI scores each listing on **affordability, low-income eligibility,
Section 8, HUD approval, transit access, utilities, and accessibility** to
surface the best options first.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Web server port |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode |
| `SECRET_KEY` | *(dev default)* | Flask session secret |
| `TWILIO_ACCOUNT_SID` | — | Twilio SID for phone/SMS |
| `TWILIO_AUTH_TOKEN` | — | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | — | Twilio outbound number |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server |
| `SMTP_USER` | — | SMTP username/email |
| `SMTP_PASSWORD` | — | SMTP password |
