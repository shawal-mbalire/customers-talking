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

SATISFACTION_PROMPT = "\n---\nWas that helpful?\n1. Yes, done\n2. No, need more help"

_POSITIVE = {"1", "yes", "y", "ok", "okay", "thanks", "thank you", "great", "good", "done"}
_NEGATIVE = {"2", "no", "nope", "not helpful", "more help", "n"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@ussd_bp.post("/ussd")
def ussd():
    session_id = request.form.get("sessionId", "")
    phone_number = request.form.get("phoneNumber", "")
    text = request.form.get("text", "").strip()

    # New session — greet and log it
    if not text:
        session = session_store.get_or_create(phone_number, "ussd", session_id)
        session.append_message("bot", GREETING)
        session_store.update(session)
        return _respond(GREETING)

    session = session_store.get_or_create(phone_number, "ussd", session_id)

    # --- Satisfaction check state machine ---
    if session.awaiting_satisfaction:
        lower = text.lower().strip()
        session.awaiting_satisfaction = False

        if lower in _POSITIVE:
            session.status = "resolved"
            session.append_message("user", text)
            session.append_message("system", "Customer confirmed satisfied — session resolved.")
            session_store.update(session)
            return _respond("END Thank you! We are glad we could help. Goodbye.")

        if lower in _NEGATIVE:
            return _escalate(session, phone_number, session_id, text,
                             reason="Customer not satisfied with automated response")

        # Ambiguous — treat as a new query, fall through
        session.append_message("user", text)

    # Direct handoff request
    if text.strip() == "0":
        session.append_message("user", "0 (requested human agent)")
        return _escalate(session, phone_number, session_id, "0",
                         reason="Customer requested a human agent directly")

    # --- Dialogflow / predefined solutions ---
    result = dialogflow_service.detect_intent(
        user_text=text, session_id=session_id, channel="ussd"
    )

    if not session.messages or session.messages[-1].get("text") != text:
        session.append_message("user", text)
    session.append_message("bot", result["text"])
    session.last_intent = result["intent_name"]
    session.last_message = text
    session.agent_reply = result["text"]

    if result["is_handoff"]:
        return _escalate(session, phone_number, session_id, text,
                         reason=result["handoff_reason"] or "Dialogflow live_agent_handoff")

    # Bot answered — set satisfaction check
    session.awaiting_satisfaction = True
    session_store.update(session)
    return _respond(f"CON {result['text']}{SATISFACTION_PROMPT}")


def _escalate(session, phone_number: str, session_id: str, user_text: str, reason: str):
    """Mark session escalated, notify customer, log to human queue."""
    session.status = "escalated"
    session.reason = reason
    session.awaiting_satisfaction = False
    session.append_message("system", f"Escalated: {reason}")
    session_store.update(session)

    human_queue.enqueue(
        EscalatedSession(
            session_id=session.session_id,
            phone_number=phone_number,
            last_intent=session.last_intent,
            reason=reason,
        )
    )

    try:
        africastalking_service.send_handoff_sms(phone_number)
    except Exception:
        pass

    return _respond("END Connecting you to a specialist. They will reach out via SMS shortly.")


def _respond(text: str):
    response = make_response(text)
    response.headers["Content-Type"] = "text/plain"
    return response
