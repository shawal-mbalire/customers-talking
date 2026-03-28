import logging
from datetime import datetime, timezone
from flask import Blueprint, make_response, request, Response
from ..services import dialogflow_service, session_store

log = logging.getLogger(__name__)
voice_bp = Blueprint("voice", __name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@voice_bp.post("/voice")
def voice_webhook():
    """Africa's Talking Voice callback endpoint."""
    try:
        return _handle_voice()
    except Exception:
        log.exception("Voice webhook error")
        return _voice_response(
            "Sorry, we are experiencing technical difficulties. Please call back later.",
            gather=False,
            end=True,
        )


def _handle_voice() -> Response:
    caller = request.form.get("callerNumber", "unknown")
    session_id = request.form.get("sessionId", "") or caller
    dtmf = request.form.get("dtmfDigits", "")

    session = session_store.get_or_create(caller, "voice", session_id)

    if not dtmf:
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

    if dtmf == "0":
        session_store.update(session)
        return _voice_response("Thank you for calling. Goodbye!", gather=False, end=True)

    result = dialogflow_service.detect_intent(dtmf, session_id, channel="voice")
    session.messages.append({"role": "user", "text": dtmf, "ts": _now()})
    session.messages.append({"role": "bot", "text": result["text"], "ts": _now()})
    session.last_intent = result["intent_name"]
    session.last_message = dtmf
    session.agent_reply = result["text"]

    if result["is_handoff"]:
        session.status = "escalated"
        session.reason = result.get("handoff_reason", "")
        session_store.update(session)
        return _voice_response(
            "Transferring you to a specialist. Please hold.",
            gather=False,
            end=True,
        )

    session_store.update(session)
    return _voice_response(result["text"], gather=True)


def _voice_response(text: str, gather: bool = True, end: bool = False) -> Response:
    # Derive callback URL from the incoming request so it always resolves to the
    # public endpoint, regardless of BASE_URL config. Cloud Run sets X-Forwarded-Proto.
    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    host = request.headers.get("X-Forwarded-Host", request.host)
    callback_url = f"{proto}://{host}/voice"

    if end:
        xml = f'<?xml version="1.0"?><Response><Say>{text}</Say><Hangup/></Response>'
    elif gather:
        xml = (
            f'<?xml version="1.0"?><Response>'
            f'<GetDigits timeout="30" finishOnKey="#" callbackUrl="{callback_url}">'
            f"<Say>{text}</Say>"
            f"</GetDigits>"
            f"<Say>We did not receive any input. Goodbye.</Say><Hangup/>"
            f"</Response>"
        )
    else:
        xml = f'<?xml version="1.0"?><Response><Say>{text}</Say></Response>'

    resp = make_response(xml)
    resp.headers["Content-Type"] = "text/xml"
    return resp
