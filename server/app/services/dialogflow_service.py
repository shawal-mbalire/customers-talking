"""
Dialogflow CX service.

Returns a dict:
  {
    "text": str,                  # bot reply
    "intent_name": str,           # matched intent display name
    "is_handoff": bool,           # True when live_agent_handoff is present
    "handoff_reason": str,        # payload reason field (if any)
  }
"""
import uuid
from flask import current_app
from google.cloud.dialogflowcx_v3beta1 import SessionsClient
from google.cloud.dialogflowcx_v3beta1.types import (
    DetectIntentRequest,
    QueryInput,
    TextInput,
)


def _build_session_path(client: SessionsClient, session_id: str) -> str:
    cfg = current_app.config
    return client.session_path(
        project=cfg["DIALOGFLOW_PROJECT_ID"],
        location=cfg["DIALOGFLOW_LOCATION"],
        agent=cfg["DIALOGFLOW_AGENT_ID"],
        session=session_id,
    )


def detect_intent(user_text: str, session_id: str | None = None, channel: str = "ussd") -> dict:
    """Send text to Dialogflow CX and parse the response.

    First checks predefined solutions. Falls back to Dialogflow CX.
    """
    from . import solutions_store

    solution = solutions_store.find_match(user_text, channel)
    if solution:
        return {
            "text": solution.answer,
            "intent_name": solution.intent_name or "predefined_solution",
            "is_handoff": False,
            "handoff_reason": "",
            "source": "predefined",
        }

    cfg = current_app.config
    session_id = session_id or str(uuid.uuid4())

    client = SessionsClient(
        client_options={"api_endpoint": f"{cfg['DIALOGFLOW_LOCATION']}-dialogflow.googleapis.com"}
    )
    session_path = _build_session_path(client, session_id)

    request = DetectIntentRequest(
        session=session_path,
        query_input=QueryInput(
            text=TextInput(text=user_text),
            language_code=cfg["DIALOGFLOW_LANGUAGE_CODE"],
        ),
    )

    response = client.detect_intent(request=request)
    query_result = response.query_result

    # --- Collect bot reply text ---
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

    return {
        "text": " ".join(reply_parts) or "I'm not sure how to help with that.",
        "intent_name": intent_name,
        "is_handoff": is_handoff,
        "handoff_reason": handoff_reason,
        "source": "dialogflow",
    }
