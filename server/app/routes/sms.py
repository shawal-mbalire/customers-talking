from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from ..services import dialogflow_service, session_store, africastalking_service

sms_bp = Blueprint("sms", __name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@sms_bp.post("/sms")
def sms_webhook():
    """Africa's Talking SMS webhook callback."""
    if request.is_json:
        data = request.get_json(force=True)
        phone = data.get("from", "")
        text = data.get("text", "")
    else:
        phone = request.form.get("from", "")
        text = request.form.get("text", "")

    session = session_store.get_or_create(phone, "sms", f"sms-{phone}")
    result = dialogflow_service.detect_intent(text, f"sms-{phone}", channel="sms")

    session.messages.append({"role": "user", "text": text, "ts": _now()})
    session.messages.append({"role": "bot", "text": result["text"], "ts": _now()})
    session.last_intent = result["intent_name"]
    session.last_message = text
    session.agent_reply = result["text"]

    if result["is_handoff"]:
        session.status = "escalated"
        session.reason = result["handoff_reason"]

    session_store.update(session)

    # Send SMS reply via Africa's Talking
    try:
        africastalking_service.send_sms(phone, result["text"])
    except Exception:
        pass

    return jsonify({"status": "ok"})
