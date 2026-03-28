from datetime import datetime, timezone
from flask import Blueprint, request, make_response
from ..services import dialogflow_service, human_queue, africastalking_service, session_store
from ..models.session import EscalatedSession

ussd_bp = Blueprint("ussd", __name__)

GREETING = (
    "CON Welcome to Customer Care.\n"
    "1. Check order status\n"
    "2. Account enquiry\n"
    "3. Report a problem\n"
    "0. Talk to a human agent"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@ussd_bp.post("/ussd")
def ussd():
    """
    Africa's Talking USSD callback endpoint.

    AT sends these form fields:
      sessionId, serviceCode, phoneNumber, text
    """
    session_id = request.form.get("sessionId", "")
    phone_number = request.form.get("phoneNumber", "")
    text = request.form.get("text", "").strip()

    # New session — text is empty on first request
    if not text:
        session = session_store.get_or_create(phone_number, "ussd", session_id)
        session.messages.append({"role": "bot", "text": GREETING, "ts": _now()})
        session_store.update(session)
        return _respond(GREETING)

    # Pass user input to Dialogflow CX
    result = dialogflow_service.detect_intent(
        user_text=text,
        session_id=session_id,
        channel="ussd",
    )

    session = session_store.get_or_create(phone_number, "ussd", session_id)
    session.messages.append({"role": "user", "text": text, "ts": _now()})
    session.messages.append({"role": "bot", "text": result["text"], "ts": _now()})
    session.last_intent = result["intent_name"]
    session.last_message = text
    session.agent_reply = result["text"]

    if result["is_handoff"]:
        session.status = "escalated"
        session.reason = result["handoff_reason"]
        session_store.update(session)

        # Log to human queue
        human_queue.enqueue(
            EscalatedSession(
                session_id=session_id,
                phone_number=phone_number,
                last_intent=result["intent_name"],
                reason=result["handoff_reason"],
            )
        )

        # Notify customer via SMS (best-effort)
        try:
            africastalking_service.send_handoff_sms(phone_number)
        except Exception:
            pass  # Don't fail the USSD session if SMS fails

        return _respond(
            "END Transferring you to a specialist. They will SMS you shortly."
        )

    session_store.update(session)
    return _respond(f"CON {result['text']}")


def _respond(text: str):
    response = make_response(text)
    response.headers["Content-Type"] = "text/plain"
    return response
