from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from ..services import dialogflow_service, session_store, africastalking_service
from ..models.session import EscalatedSession

sms_bp = Blueprint("sms", __name__)

SMS_SATISFACTION_PROMPT = "\n\nReply YES if that helped, or NO for more assistance."

_POSITIVE = {"yes", "y", "1", "ok", "okay", "thanks", "thank you", "great", "perfect", "good"}
_NEGATIVE = {"no", "n", "2", "not helpful", "more help", "nope", "didnt help", "didn't help"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@sms_bp.post("/sms")
def sms_webhook():
    if request.is_json:
        data = request.get_json(force=True)
        phone, text = data.get("from", ""), data.get("text", "")
    else:
        phone, text = request.form.get("from", ""), request.form.get("text", "")

    text = text.strip()
    session = session_store.get_or_create(phone, "sms", f"sms-{phone}")

    # --- Satisfaction check ---
    if session.awaiting_satisfaction:
        lower = text.lower().strip()
        session.awaiting_satisfaction = False

        if lower in _POSITIVE:
            session.status = "resolved"
            session.append_message("user", text)
            session.append_message("system", "Customer confirmed satisfied — session resolved.")
            session_store.update(session)
            try:
                africastalking_service.send_sms(phone, "Great! Glad we could help. Contact us anytime.")
            except Exception:
                pass
            return jsonify({"status": "ok"})

        if lower in _NEGATIVE:
            session.status = "escalated"
            session.reason = "Customer not satisfied with automated SMS response"
            session.append_message("user", text)
            session.append_message("system", "Escalated: Customer not satisfied")
            session_store.update(session)
            try:
                africastalking_service.send_sms(
                    phone,
                    "We're connecting you to a live agent. They will contact you shortly."
                )
            except Exception:
                pass
            return jsonify({"status": "ok"})

        # Ambiguous — fall through as new query

    # --- Dialogflow / predefined solutions ---
    result = dialogflow_service.detect_intent(text, f"sms-{phone}", channel="sms")

    session.append_message("user", text)
    session.append_message("bot", result["text"])
    session.last_intent = result["intent_name"]
    session.last_message = text
    session.agent_reply = result["text"]

    if result["is_handoff"]:
        session.status = "escalated"
        session.reason = result["handoff_reason"] or "Dialogflow live_agent_handoff"
        session.awaiting_satisfaction = False
        session.append_message("system", f"Escalated: {session.reason}")
        session_store.update(session)
        try:
            africastalking_service.send_sms(
                phone,
                "Our agent will contact you shortly. Thank you for your patience."
            )
        except Exception:
            pass
        return jsonify({"status": "ok"})

    # Bot answered — set satisfaction check
    session.awaiting_satisfaction = True
    session_store.update(session)

    try:
        africastalking_service.send_sms(phone, result["text"] + SMS_SATISFACTION_PROMPT)
    except Exception:
        pass

    return jsonify({"status": "ok"})
