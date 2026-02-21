"""
Agent Caller / Contact Module
Connects users with real estate agents via phone (Twilio) or email (SMTP).
Generates multilingual call scripts and email templates.
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional Twilio import for automated phone calls / SMS
# ---------------------------------------------------------------------------
try:
    from twilio.rest import Client as TwilioClient
    _TWILIO_AVAILABLE = True
except ImportError:
    _TWILIO_AVAILABLE = False
    logger.info("twilio package not installed — phone call feature disabled.")

# ---------------------------------------------------------------------------
# Multilingual greeting templates
# ---------------------------------------------------------------------------
GREETINGS = {
    "English": (
        "Hello, my name is Alex, a virtual housing assistant. "
        "I am calling on behalf of {user_name} who is looking for affordable housing. "
        "They are interested in the property at {address} listed at ${rent}/month. "
        "Could you please provide more information or schedule a viewing? "
        "Their contact number is {user_phone}. Thank you."
    ),
    "Spanish": (
        "Hola, me llamo Alex, soy un asistente virtual de vivienda. "
        "Llamo en nombre de {user_name}, quien busca vivienda asequible. "
        "Está interesado/a en la propiedad en {address} listada a ${rent}/mes. "
        "¿Podría proporcionarme más información o programar una visita? "
        "Su número de contacto es {user_phone}. Gracias."
    ),
    "French": (
        "Bonjour, je m'appelle Alex, assistant virtuel en immobilier. "
        "J'appelle au nom de {user_name} qui recherche un logement abordable. "
        "Il/Elle est intéressé(e) par le bien au {address} affiché à ${rent}/mois. "
        "Pourriez-vous fournir plus d'informations ou planifier une visite? "
        "Son numéro de contact est {user_phone}. Merci."
    ),
    "Amharic": (
        "ሰላም፣ ስሜ አሌክስ ነው፣ ምናባዊ የቤቶች ረዳት ነኝ። "
        "በ{user_name} ስም እደውልሃለሁ፣ ተመጣጣኝ ቤት እየፈለጉ ነው። "
        "በ{address} ያለውን ቤት ${rent}/ወር ፍላጎት አላቸው። "
        "ተጨማሪ መረጃ ወይም ጉብኝት ማዘጋጀት ይችላሉ? "
        "የእርሳቸው ስልክ ቁጥር {user_phone} ነው። አስቀድሜ አመሰግናለሁ።"
    ),
}

# Email templates per language
EMAIL_SUBJECTS = {
    "English": "Affordable Housing Inquiry — {address}",
    "Spanish": "Consulta sobre vivienda asequible — {address}",
    "French": "Demande de logement abordable — {address}",
    "Amharic": "ተመጣጣኝ ቤት ጥያቄ — {address}",
}

EMAIL_BODIES = {
    "English": (
        "Dear {agent_name},\n\n"
        "My name is {user_name} and I am looking for affordable housing. "
        "I found your listing at {address}, {city}, {state} for ${rent}/month "
        "and I am very interested.\n\n"
        "Could you please contact me at {user_phone} or {user_email} to discuss "
        "availability and schedule a viewing?\n\n"
        "Thank you for your time.\n\n"
        "Best regards,\n{user_name}"
    ),
    "Spanish": (
        "Estimado/a {agent_name},\n\n"
        "Me llamo {user_name} y estoy buscando vivienda asequible. "
        "Encontré su propiedad en {address}, {city}, {state} por ${rent}/mes "
        "y estoy muy interesado/a.\n\n"
        "¿Podría contactarme en {user_phone} o {user_email} para hablar sobre "
        "disponibilidad y coordinar una visita?\n\n"
        "Gracias por su tiempo.\n\n"
        "Atentamente,\n{user_name}"
    ),
}


class AgentCaller:
    """Handles contacting real estate agents on behalf of a housing seeker."""

    def __init__(
        self,
        twilio_account_sid: str = None,
        twilio_auth_token: str = None,
        twilio_phone_number: str = None,
        smtp_host: str = None,
        smtp_port: int = 587,
        smtp_user: str = None,
        smtp_password: str = None,
    ):
        # Twilio credentials (fall back to env vars)
        self.twilio_sid = twilio_account_sid or os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_token = twilio_auth_token or os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_phone = twilio_phone_number or os.getenv("TWILIO_PHONE_NUMBER", "")
        # SMTP credentials (fall back to env vars)
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")

    # ------------------------------------------------------------------
    # Script / message generation
    # ------------------------------------------------------------------

    def build_call_script(
        self,
        listing: dict,
        user_name: str,
        user_phone: str,
        preferred_language: str = "English",
    ) -> str:
        """Return a call script in the preferred language."""
        template = GREETINGS.get(preferred_language, GREETINGS["English"])
        return template.format(
            user_name=user_name,
            address=listing.get("address", "the listed property"),
            rent=listing.get("monthly_rent", "N/A"),
            user_phone=user_phone,
        )

    def build_email(
        self,
        listing: dict,
        user_name: str,
        user_phone: str,
        user_email: str,
        preferred_language: str = "English",
    ) -> dict:
        """Return a dict with ``subject`` and ``body`` ready to send."""
        subject_template = EMAIL_SUBJECTS.get(
            preferred_language, EMAIL_SUBJECTS["English"]
        )
        body_template = EMAIL_BODIES.get(
            preferred_language, EMAIL_BODIES["English"]
        )
        context = dict(
            agent_name=listing.get("agent_name", "Agent"),
            user_name=user_name,
            address=listing.get("address", "the listed property"),
            city=listing.get("city", ""),
            state=listing.get("state", ""),
            rent=listing.get("monthly_rent", "N/A"),
            user_phone=user_phone,
            user_email=user_email,
        )
        return {
            "subject": subject_template.format(**context),
            "body": body_template.format(**context),
        }

    # ------------------------------------------------------------------
    # Twilio phone call
    # ------------------------------------------------------------------

    def call_agent(
        self,
        agent_phone: str,
        script: str,
        from_number: str = None,
    ) -> dict:
        """Initiate a phone call to the agent with the provided TwiML script.

        Returns a dict with ``success`` bool and ``sid`` or ``error`` key.
        """
        if not _TWILIO_AVAILABLE:
            logger.warning("Twilio not installed — cannot make phone calls.")
            return {"success": False, "error": "Twilio not available."}
        if not (self.twilio_sid and self.twilio_token and self.twilio_phone):
            logger.warning("Twilio credentials not configured.")
            return {
                "success": False,
                "error": "Twilio credentials not configured. "
                         "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
                         "TWILIO_PHONE_NUMBER environment variables.",
            }
        try:
            client = TwilioClient(self.twilio_sid, self.twilio_token)
            twiml = (
                f"<Response><Say>{script}</Say>"
                "<Pause length='2'/>"
                "<Say>Goodbye.</Say></Response>"
            )
            call = client.calls.create(
                twiml=twiml,
                to=agent_phone,
                from_=from_number or self.twilio_phone,
            )
            logger.info("Call initiated: %s", call.sid)
            return {"success": True, "sid": call.sid}
        except Exception as exc:
            logger.error("Call failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def send_sms(
        self,
        agent_phone: str,
        message: str,
        from_number: str = None,
    ) -> dict:
        """Send an SMS to the agent."""
        if not _TWILIO_AVAILABLE:
            return {"success": False, "error": "Twilio not available."}
        if not (self.twilio_sid and self.twilio_token and self.twilio_phone):
            return {"success": False, "error": "Twilio credentials not configured."}
        try:
            client = TwilioClient(self.twilio_sid, self.twilio_token)
            msg = client.messages.create(
                body=message[:1600],
                from_=from_number or self.twilio_phone,
                to=agent_phone,
            )
            return {"success": True, "sid": msg.sid}
        except Exception as exc:
            logger.error("SMS failed: %s", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------

    def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        from_address: str = None,
    ) -> dict:
        """Send an email via SMTP."""
        sender = from_address or self.smtp_user
        if not (self.smtp_host and sender and self.smtp_password):
            logger.warning("SMTP credentials not configured.")
            return {
                "success": False,
                "error": "SMTP credentials not configured. "
                         "Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD environment variables.",
            }
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = to_address
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(sender, to_address, msg.as_string())
            logger.info("Email sent to %s", to_address)
            return {"success": True}
        except Exception as exc:
            logger.error("Email failed: %s", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # High-level helper
    # ------------------------------------------------------------------

    def contact_agent_for_listing(
        self,
        listing: dict,
        user_name: str,
        user_phone: str,
        user_email: str = "",
        preferred_language: str = "English",
        method: str = "email",
    ) -> dict:
        """Contact the listing's agent via ``method`` (``"call"``, ``"sms"``,
        or ``"email"``) using localised templates.

        Returns a result dict from the underlying transport.
        """
        agent_phone = listing.get("agent_phone", "")
        agent_email = listing.get("agent_email", "")

        if method == "call":
            script = self.build_call_script(
                listing, user_name, user_phone, preferred_language
            )
            return self.call_agent(agent_phone, script)

        elif method == "sms":
            script = self.build_call_script(
                listing, user_name, user_phone, preferred_language
            )
            return self.send_sms(agent_phone, script[:1600])

        else:  # email (default)
            if not agent_email:
                return {"success": False, "error": "No agent email for this listing."}
            email = self.build_email(
                listing, user_name, user_phone, user_email, preferred_language
            )
            return self.send_email(agent_email, email["subject"], email["body"])
