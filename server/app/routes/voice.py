from datetime import datetime, timezone
from flask import Blueprint, current_app, make_response, request, Response
from ..services import dialogflow_service, session_store

voice_bp = Blueprint("voice", __name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@voice_bp.post("/voice")
def voice_webhook():
    """Africa's Talking Voice callback endpoint."""
    caller = request.form.get("callerNumber", "")
    session_id = request.form.get("sessionId", "")
    dtmf = request.form.get("dtmfDigits", "")

    session = session_store.get_or_create(caller, "voice", session_id)

    if not dtmf:
        # First call — greet the caller
        reply_text = (
            "Welcome to Customer Care. "
            "Press 1 for order status. "
            "Press 2 for account help. "
            "Press 3 to speak to an agent. "
            "Press 0 to hang up."
        )
        session.messages.append({"role": "bot", "text": reply_text, "ts": _now()})
        session_store.update(session)
        return _voice_response(reply_text, gather=True)

    result = dialogflow_service.detect_intent(dtmf, session_id, channel="voice")
    session.messages.append({"role": "user", "text": dtmf, "ts": _now()})
    session.messages.append({"role": "bot", "text": result["text"], "ts": _now()})
    session.last_intent = result["intent_name"]
    session.last_message = dtmf
    session.agent_reply = result["text"]

    if result["is_handoff"]:
        session.status = "escalated"
        session.reason = result["handoff_reason"]
        session_store.update(session)
        return _voice_response(
            "Transferring you to a specialist. Please hold.",
            gather=False,
            end=True,
        )

    session_store.update(session)
    return _voice_response(result["text"], gather=True)


def _voice_response(text: str, gather: bool = True, end: bool = False) -> Response:
    base_url = current_app.config.get("BASE_URL", "http://localhost:5000")
    if end:
        xml = f'<?xml version="1.0"?><Response><Say>{text}</Say><Hangup/></Response>'
    elif gather:
        xml = (
            f'<?xml version="1.0"?><Response>'
            f'<GetDigits timeout="30" finishOnKey="#" callbackUrl="{base_url}/voice">'
            f"<Say>{text}</Say>"
            f"</GetDigits></Response>"
        )
    else:
        xml = f'<?xml version="1.0"?><Response><Say>{text}</Say></Response>'
    resp = make_response(xml)
    resp.headers["Content-Type"] = "text/xml"
    return resp
