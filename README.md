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

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the web app

```bash
python app.py
# Open http://localhost:5000
```

### 3. Run the CLI chatbot

```bash
python -c "from src.chatbot import Chatbot; Chatbot().run_cli()"
```

### 4. Enable voice in CLI (optional)

```bash
# Install audio packages first
pip install SpeechRecognition pyttsx3

python -c "from src.chatbot import Chatbot; Chatbot(voice_enabled=True).run_cli()"
```

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

## Housing Dataset

The dataset (`data/housing_data.csv`) covers the **Atlanta metro area** and includes:
- Monthly rent, bedrooms, bathrooms, square footage
- Section 8 acceptance, HUD approval, low-income eligibility, AMI % limit
- Transit access, utilities included, pet policy, accessibility features
- Agent name, phone, email, and languages spoken

The AI scores each listing on **affordability, low-income eligibility, Section 8, HUD approval, transit access, utilities, and accessibility** to surface the best options first.

---

## Running Tests

```bash
pytest tests/ -v
```

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
