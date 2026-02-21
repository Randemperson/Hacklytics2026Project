"""
Chatbot Controller
Orchestrates the HousingAI, VoiceInterface, and AgentCaller into a
conversational loop that can run in the terminal or be driven by the
web API.
"""
import logging
from typing import Optional

from .housing_ai import HousingAI
from .agent_caller import AgentCaller
from .voice_interface import VoiceInterface

logger = logging.getLogger(__name__)

WELCOME_MESSAGE = (
    "Welcome to the Real Estate AI Assistant! "
    "I help immigrants and minorities find affordable housing in your area. "
    "You can ask me things like:\n"
    "  • 'Find 2-bedroom apartments under $800 in Atlanta'\n"
    "  • 'Show me Section 8 housing in Decatur'\n"
    "  • 'I need wheelchair-accessible housing with Spanish-speaking agents'\n"
    "  • 'Contact agent for listing 1'\n\n"
    "Type 'quit' or say 'exit' to leave.\n"
)

CONTACT_PROMPT = (
    "To contact the agent, please provide:\n"
    "  Your name: "
)


class Chatbot:
    """Multi-turn conversational housing assistant."""

    def __init__(
        self,
        housing_ai: HousingAI = None,
        agent_caller: AgentCaller = None,
        voice: VoiceInterface = None,
        voice_enabled: bool = False,
        language: str = "en",
    ):
        self.ai = housing_ai or HousingAI()
        self.caller = agent_caller or AgentCaller()
        self.voice_enabled = voice_enabled
        self.language = language

        if voice_enabled:
            self.voice = voice or VoiceInterface(language=language)
        else:
            self.voice = None

        # Conversation state
        self._last_results = None  # last search results DataFrame
        self._session: dict = {}   # arbitrary session data

    # ------------------------------------------------------------------
    # Core turn processing
    # ------------------------------------------------------------------

    def process_turn(self, user_input: str) -> str:
        """Process one conversation turn and return the assistant's reply."""
        text = user_input.strip()
        if not text:
            return "I didn't catch that. Could you please repeat?"

        lower = text.lower()

        # --- Exit ---
        if lower in ("quit", "exit", "bye", "goodbye"):
            return "Goodbye! Good luck with your housing search. 🏠"

        # --- Contact agent ---
        if lower.startswith("contact") or "call agent" in lower or "email agent" in lower:
            return self._handle_contact_request(text)

        # --- Help ---
        if lower in ("help", "?", "what can you do"):
            return WELCOME_MESSAGE

        # --- Housing search ---
        response = self.ai.answer_query(text)
        self._last_results = response["results"]
        return response["summary"]

    def _handle_contact_request(self, text: str) -> str:
        """Guide the user through contacting an agent for a listing."""
        if self._last_results is None or self._last_results.empty:
            return (
                "Please search for a listing first, then say 'contact agent' "
                "to reach out about a specific property."
            )
        # Use the top result
        listing = self._last_results.iloc[0].to_dict()
        return (
            f"I can contact {listing['agent_name']} at {listing['agent_phone']} "
            f"or {listing['agent_email']} about {listing['address']}.\n\n"
            "To proceed, use the /contact endpoint on the web app, or call "
            f"{listing['agent_phone']} directly."
        )

    # ------------------------------------------------------------------
    # Interactive CLI loop
    # ------------------------------------------------------------------

    def run_cli(self):
        """Start an interactive command-line session."""
        print(WELCOME_MESSAGE)
        if self.voice and self.voice.is_tts_available:
            self.voice.speak(
                "Welcome to the Real Estate AI Assistant. "
                "How can I help you find affordable housing today?"
            )

        while True:
            try:
                # --- Get input (voice or keyboard) ---
                if self.voice_enabled and self.voice and self.voice.is_mic_available:
                    print("Listening… (or type your query): ", end="", flush=True)
                    spoken = self.voice.listen(timeout=8)
                    if spoken:
                        print(spoken)
                        user_input = spoken
                    else:
                        user_input = input()
                else:
                    user_input = input("You: ")

                # --- Process ---
                reply = self.process_turn(user_input)
                print(f"\nAssistant: {reply}\n")

                # --- Speak reply ---
                if self.voice and self.voice.is_tts_available:
                    # Truncate long replies for speech
                    speech_text = reply[:500] if len(reply) > 500 else reply
                    self.voice.speak(speech_text)

                if reply.startswith("Goodbye"):
                    break

            except KeyboardInterrupt:
                print("\nAssistant: Goodbye! 🏠")
                break
            except EOFError:
                break
