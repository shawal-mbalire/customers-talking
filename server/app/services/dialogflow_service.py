"""
Dialogflow CX service.

Returns a dict:
  {
    "text": str,                  # bot reply
    "intent_name": str,           # matched intent display name
    "is_handoff": bool,           # True when live_agent_handoff is present
    "handoff_reason": str,        # payload reason field (if any)
    "source": str,                # "predefined" | "dialogflow" | "fallback"
  }
"""
import logging
import uuid
from flask import current_app
from google.oauth2 import service_account
from google.cloud.dialogflowcx_v3beta1 import SessionsClient
from google.cloud.dialogflowcx_v3beta1.types import (
    DetectIntentRequest,
    QueryInput,
    TextInput,
)

log = logging.getLogger(__name__)
_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

_FALLBACK = {
    "text": "I'm not sure how to help with that. Please hold while we connect you to an agent.",
    "intent_name": "fallback",
    "is_handoff": True,
    "handoff_reason": "Dialogflow unavailable",
    "source": "fallback",
}


def _get_credentials() -> service_account.Credentials:
    cfg = current_app.config
    email = cfg["GOOGLE_SERVICE_ACCOUNT_EMAIL"]
    private_key = cfg["GOOGLE_PRIVATE_KEY"]
    private_key_id = cfg["GOOGLE_PRIVATE_KEY_ID"]

    if not email or not private_key:
        raise ValueError(
            f"Missing Google credentials: email={bool(email)}, key={bool(private_key)}"
        )

    info = {
        "type": "service_account",
        "project_id": cfg["DIALOGFLOW_PROJECT_ID"],
        "private_key_id": private_key_id,
        "private_key": private_key,
        "client_email": email,
        "client_id": "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": (
            f"https://www.googleapis.com/robot/v1/metadata/x509/{email.replace('@', '%40')}"
        ),
    }
    log.debug("Building credentials for %s", email)
    return service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)


def _build_session_path(client: SessionsClient, session_id: str) -> str:
    cfg = current_app.config
    project = cfg["DIALOGFLOW_PROJECT_ID"]
    location = cfg["DIALOGFLOW_LOCATION"]
    agent = cfg["DIALOGFLOW_AGENT_ID"]
    log.debug("Session path: project=%s location=%s agent=%s session=%s", project, location, agent, session_id)
    return client.session_path(
        project=project,
        location=location,
        agent=agent,
        session=session_id,
    )


def detect_intent(user_text: str, session_id: str | None = None, channel: str = "ussd") -> dict:
    """Send text to Dialogflow CX. Falls back to predefined solutions first."""
    from . import solutions_store

    # 1. Check predefined solutions
    solution = solutions_store.find_match(user_text, channel)
    if solution:
        log.debug("Predefined solution matched: %s", solution.intent_name)
        return {
            "text": solution.answer,
            "intent_name": solution.intent_name or "predefined_solution",
            "is_handoff": False,
            "handoff_reason": "",
            "source": "predefined",
        }

    cfg = current_app.config
    session_id = session_id or str(uuid.uuid4())

    # 2. Validate required config before attempting Dialogflow call
    missing = [k for k in ("DIALOGFLOW_PROJECT_ID", "DIALOGFLOW_AGENT_ID", "GOOGLE_SERVICE_ACCOUNT_EMAIL", "GOOGLE_PRIVATE_KEY") if not cfg.get(k)]
    if missing:
        log.error("Dialogflow config missing: %s — returning fallback", missing)
        return _FALLBACK

    try:
        credentials = _get_credentials()
        api_endpoint = f"{cfg['DIALOGFLOW_LOCATION']}-dialogflow.googleapis.com"
        log.info("Calling Dialogflow CX at %s", api_endpoint)

        client = SessionsClient(
            credentials=credentials,
            client_options={"api_endpoint": api_endpoint},
        )
        session_path = _build_session_path(client, session_id)

        df_request = DetectIntentRequest(
            session=session_path,
            query_input=QueryInput(
                text=TextInput(text=user_text),
                language_code=cfg["DIALOGFLOW_LANGUAGE_CODE"],
            ),
        )

        response = client.detect_intent(request=df_request)
        query_result = response.query_result

        reply_parts: list[str] = []
        is_handoff = False
        handoff_reason = ""

        for message in query_result.response_messages:
            if message.live_agent_handoff:
                is_handoff = True
                metadata = message.live_agent_handoff.metadata
                handoff_reason = metadata.get("reason", "") if metadata else ""
            if message.text.text:
                reply_parts.extend(message.text.text)

        intent_name = getattr(query_result.intent, "display_name", "unknown")
        reply_text = " ".join(reply_parts) or "I'm not sure how to help with that."
        log.info("Dialogflow intent=%s handoff=%s", intent_name, is_handoff)

        return {
            "text": reply_text,
            "intent_name": intent_name,
            "is_handoff": is_handoff,
            "handoff_reason": handoff_reason,
            "source": "dialogflow",
        }

    except Exception:
        log.exception("Dialogflow CX call failed for text=%r session=%s", user_text, session_id)
        return _FALLBACK
