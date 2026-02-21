"""
Voice Interface Module
Provides speech-to-text (microphone input) and text-to-speech (audio output)
so the housing assistant can be fully voice-activated.
"""
import logging
import os

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy imports — gracefully degrade when running in headless / CI
# environments where audio devices are not available.
# ---------------------------------------------------------------------------
try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False
    logger.warning("speech_recognition not installed — microphone input disabled.")

try:
    import pyttsx3
    _TTS_AVAILABLE = True
except ImportError:
    _TTS_AVAILABLE = False
    logger.warning("pyttsx3 not installed — text-to-speech output disabled.")

try:
    from gtts import gTTS
    import io
    _GTTS_AVAILABLE = True
except ImportError:
    _GTTS_AVAILABLE = False


class VoiceInterface:
    """Wraps microphone input and text-to-speech output.

    Falls back to printing/returning text when audio hardware is unavailable.
    """

    def __init__(self, language: str = "en", tts_backend: str = "auto"):
        """
        Args:
            language: BCP-47 language code used for both STT and TTS
                      (e.g. ``"en"``, ``"es"``, ``"zh-CN"``).
            tts_backend: ``"pyttsx3"``, ``"gtts"``, or ``"auto"`` (tries
                         pyttsx3 first, then gTTS, then silent fallback).
        """
        self.language = language
        self.tts_backend = tts_backend
        self._recogniser = None
        self._tts_engine = None
        self._init_recogniser()
        self._init_tts()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_recogniser(self):
        if _SR_AVAILABLE:
            self._recogniser = sr.Recognizer()
            self._recogniser.energy_threshold = 300
            self._recogniser.dynamic_energy_threshold = True

    def _init_tts(self):
        if self.tts_backend in ("pyttsx3", "auto") and _TTS_AVAILABLE:
            try:
                self._tts_engine = pyttsx3.init()
                rate = self._tts_engine.getProperty("rate")
                self._tts_engine.setProperty("rate", max(120, rate - 20))
            except Exception as exc:
                logger.warning("pyttsx3 init failed: %s", exc)
                self._tts_engine = None

    # ------------------------------------------------------------------
    # Speech-to-text
    # ------------------------------------------------------------------

    def listen(self, timeout: int = 10, phrase_limit: int = 15) -> str:
        """Listen on the default microphone and return recognised text.

        Returns an empty string when no audio device is available or
        the speech could not be recognised.
        """
        if not _SR_AVAILABLE or self._recogniser is None:
            logger.info("Microphone not available — returning empty string.")
            return ""
        try:
            with sr.Microphone() as source:
                logger.info("Adjusting for ambient noise…")
                self._recogniser.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Listening…")
                audio = self._recogniser.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
            text = self._recogniser.recognize_google(
                audio, language=self.language
            )
            logger.info("Heard: %s", text)
            return text
        except sr.WaitTimeoutError:
            logger.info("No speech detected within timeout.")
            return ""
        except sr.UnknownValueError:
            logger.info("Speech not recognised.")
            return ""
        except sr.RequestError as exc:
            logger.error("Speech recognition service error: %s", exc)
            return ""
        except Exception as exc:
            logger.error("listen() error: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Text-to-speech
    # ------------------------------------------------------------------

    def speak(self, text: str, save_path: str = None) -> bool:
        """Convert ``text`` to speech.

        Args:
            text: The message to speak aloud.
            save_path: Optional file path (e.g. ``"/tmp/response.mp3"``) to
                       save the audio for later playback.

        Returns:
            ``True`` if audio was played/saved, ``False`` otherwise.
        """
        if not text:
            return False

        # --- pyttsx3 (offline, real-time) ---
        if self._tts_engine is not None:
            try:
                if save_path:
                    self._tts_engine.save_to_file(text, save_path)
                    self._tts_engine.runAndWait()
                else:
                    self._tts_engine.say(text)
                    self._tts_engine.runAndWait()
                return True
            except Exception as exc:
                logger.warning("pyttsx3 speak failed: %s", exc)

        # --- gTTS (online, supports many languages) ---
        if _GTTS_AVAILABLE:
            try:
                tts = gTTS(text=text, lang=self.language[:2], slow=False)
                if save_path:
                    tts.save(save_path)
                else:
                    tmp = "/tmp/_housing_ai_tts.mp3"
                    tts.save(tmp)
                    os.system(f"mpg123 -q {tmp} 2>/dev/null || "
                              f"afplay {tmp} 2>/dev/null || "
                              f"ffplay -nodisp -autoexit {tmp} 2>/dev/null")
                return True
            except Exception as exc:
                logger.warning("gTTS speak failed: %s", exc)

        # --- Silent fallback ---
        logger.info("[TTS fallback] %s", text)
        print(f"[Assistant]: {text}")
        return False

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def set_language(self, language: str):
        """Switch the recognition/speech language at runtime."""
        self.language = language

    @property
    def is_mic_available(self) -> bool:
        return _SR_AVAILABLE and self._recogniser is not None

    @property
    def is_tts_available(self) -> bool:
        return self._tts_engine is not None or _GTTS_AVAILABLE
