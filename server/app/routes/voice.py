import logging
import base64
from datetime import datetime, timezone
from flask import Blueprint, make_response, request, Response
from ..services import dialogflow_service, session_store, detect_intent_with_audio
from ..services.audio_service import (
    download_audio_recording,
    transcribe_audio_with_google_speech,
    validate_audio_format,
)

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


@voice_bp.post("/voice/callback")
def voice_callback():
    """
    Africa's Talking Voice callback for handling recorded audio.
    
    This endpoint receives the recording URL after a call recording is complete.
    It downloads the audio, transcribes it, and sends it to Dialogflow for intent detection.
    """
    try:
        return _handle_voice_callback()
    except Exception:
        log.exception("Voice callback error")
        return _voice_response("Error processing voice input", gather=False, end=True)


def _handle_voice_callback() -> Response:
    """
    Handle voice recording callback from Africa's Talking.
    
    Africa's Talking sends:
    - recordingUrl: URL to the recorded audio
    - sessionId: Unique session identifier
    - callerNumber: Caller's phone number
    """
    recording_url = request.form.get("recordingUrl", "")
    session_id = request.form.get("sessionId", "")
    caller_number = request.form.get("callerNumber", "unknown")
    
    if not recording_url:
        log.warning("No recording URL provided in callback")
        return _voice_response("", gather=False, end=True)
    
    log.info("Processing voice recording for session %s from %s", session_id, caller_number)
    
    # Get or create session
    session = session_store.get_or_create(caller_number, "voice", session_id)
    
    # Download the audio recording
    audio_content = download_audio_recording(recording_url)
    if not audio_content:
        log.error("Failed to download audio recording")
        session.messages.append({"role": "bot", "text": "Sorry, I couldn't process your voice message. Please try again.", "ts": _now()})
        session_store.update(session)
        return _voice_response("Sorry, I couldn't process your voice message. Please try again.", gather=False, end=True)
    
    # Validate audio format
    audio_info = validate_audio_format(audio_content)
    log.info("Audio format: %s", audio_info)
    
    # Send audio directly to Dialogflow CX for speech recognition and intent detection
    result = detect_intent_with_audio(
        audio_content=audio_content,
        session_id=session_id,
        channel="voice",
        sample_rate_hertz=audio_info.get("sample_rate", 16000) or 16000,
    )
    
    # Get the transcribed text (from Dialogflow or fallback)
    user_text = result.get("transcribed_text", "voice input")
    
    # Log the conversation
    session.messages.append({"role": "user", "text": f"[Voice] {user_text}", "ts": _now()})
    session.messages.append({"role": "bot", "text": result["text"], "ts": _now()})
    session.last_intent = result["intent_name"]
    session.last_message = user_text
    session.agent_reply = result["text"]
    
    # Handle escalation
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
    
    # Continue the conversation with voice response
    return _voice_response(result["text"], gather=True)


def _handle_voice() -> Response:
    caller = request.form.get("callerNumber", "unknown")
    session_id = request.form.get("sessionId", "") or caller
    dtmf = request.form.get("dtmfDigits", "")
    # Africa's Talking may also send recordingUrl for recorded voice input
    recording_url = request.form.get("recordingUrl", "")

    session = session_store.get_or_create(caller, "voice", session_id)

    # Handle voice recording if available
    if recording_url:
        log.info("Processing voice recording for session %s", session_id)
        return _process_voice_recording(recording_url, session, session_id)

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


def _process_voice_recording(recording_url: str, session, session_id: str) -> Response:
    """
    Process a voice recording from Africa's Talking.
    
    Downloads the audio, transcribes it using Google Speech-to-Text,
    and sends the transcription to Dialogflow for intent detection.
    """
    from ..services import dialogflow_service
    
    # Download the audio recording
    from ..services.audio_service import download_audio_recording, validate_audio_format
    audio_content = download_audio_recording(recording_url)
    
    if not audio_content:
        log.error("Failed to download audio recording from %s", recording_url)
        session.messages.append({"role": "bot", "text": "Sorry, I couldn't process your voice message.", "ts": _now()})
        session_store.update(session)
        return _voice_response("Sorry, I couldn't process your voice message.", gather=True)
    
    # Validate audio format
    audio_info = validate_audio_format(audio_content)
    log.info("Audio format validation: %s", audio_info)
    
    # Option 1: Use Google Speech-to-Text for transcription, then send text to Dialogflow
    # This gives more control over transcription settings
    transcribed_text = transcribe_audio_with_google_speech(
        audio_content=audio_content,
        sample_rate_hertz=audio_info.get("sample_rate", 16000) or 16000,
        language_code="en-US",  # Could be configurable
        model="phone_call",  # Optimized for telephone audio
    )
    
    if not transcribed_text:
        log.warning("Speech-to-Text transcription failed, using fallback")
        session.messages.append({"role": "bot", "text": "Sorry, I didn't catch that. Could you please repeat?", "ts": _now()})
        session_store.update(session)
        return _voice_response("Sorry, I didn't catch that. Could you please repeat?", gather=True)
    
    log.info("Transcribed voice input: %r", transcribed_text)
    
    # Send transcribed text to Dialogflow for intent detection
    result = dialogflow_service.detect_intent(transcribed_text, session_id, channel="voice")
    
    # Log the conversation
    session.messages.append({"role": "user", "text": f"[Voice] {transcribed_text}", "ts": _now()})
    session.messages.append({"role": "bot", "text": result["text"], "ts": _now()})
    session.last_intent = result["intent_name"]
    session.last_message = transcribed_text
    session.agent_reply = result["text"]
    
    # Handle escalation to human agent
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
    """
    Create a VoiceXML response for Africa's Talking.
    
    Args:
        text: Text to speak to the caller
        gather: Whether to gather DTMF input after speaking
        end: Whether to end the call after speaking
    """
    # Derive callback URL from the incoming request so it always resolves to the
    # public endpoint, regardless of BASE_URL config. Cloud Run sets X-Forwarded-Proto.
    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    host = request.headers.get("X-Forwarded-Host", request.host)
    callback_url = f"{proto}://{host}/voice"

    if end:
        # Africa's Talking ends the call when Response has no more actions
        xml = f'<?xml version="1.0"?><Response><Say>{text}</Say></Response>'
    elif gather:
        xml = (
            f'<?xml version="1.0"?><Response>'
            f'<GetDigits timeout="30" finishOnKey="#" callbackUrl="{callback_url}">'
            f"<Say>{text}</Say>"
            f"</GetDigits>"
            f"<Say>We did not receive any input. Goodbye.</Say>"
            f"</Response>"
        )
    else:
        xml = f'<?xml version="1.0"?><Response><Say>{text}</Say></Response>'

    resp = make_response(xml)
    resp.headers["Content-Type"] = "text/xml"
    return resp
