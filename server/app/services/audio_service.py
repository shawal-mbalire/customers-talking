"""
Audio processing service for handling voice recordings and speech-to-text.

This service handles:
- Downloading audio recordings from Africa's Talking
- Converting audio formats if needed
- Transcribing audio using Google Cloud Speech-to-Text
- Sending audio to Dialogflow CX for integrated speech recognition
"""
import logging
import tempfile
import os
from pathlib import Path
from typing import Optional
import requests
from google.oauth2 import service_account
from google.cloud import speech
from google.cloud.speech import RecognitionConfig, RecognitionAudio

log = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def _get_speech_credentials(app_config) -> service_account.Credentials:
    """Get Google Cloud credentials for Speech-to-Text API."""
    email = app_config["GOOGLE_SERVICE_ACCOUNT_EMAIL"]
    private_key = app_config["GOOGLE_PRIVATE_KEY"]
    private_key_id = app_config["GOOGLE_PRIVATE_KEY_ID"]
    project_id = app_config["DIALOGFLOW_PROJECT_ID"]

    if not email or not private_key:
        raise ValueError(
            f"Missing Google credentials: email={bool(email)}, key={bool(private_key)}"
        )

    info = {
        "type": "service_account",
        "project_id": project_id,
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
    log.debug("Building Speech-to-Text credentials for %s", email)
    return service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)


def download_audio_recording(recording_url: str) -> Optional[bytes]:
    """
    Download an audio recording from a URL.
    
    Africa's Talking provides call recordings via URL after a call ends.
    
    Args:
        recording_url: Public URL to the audio file
        
    Returns:
        Audio file bytes or None if download fails
    """
    try:
        log.info("Downloading audio recording from %s", recording_url)
        response = requests.get(recording_url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        log.error("Failed to download audio recording: %s", e)
        return None


def transcribe_audio_with_google_speech(
    audio_content: bytes,
    sample_rate_hertz: int = 16000,
    language_code: str = "en-US",
    enable_automatic_punctuation: bool = True,
    model: str = "phone_call",
) -> Optional[str]:
    """
    Transcribe audio using Google Cloud Speech-to-Text API.
    
    Args:
        audio_content: Raw audio bytes (WAV format)
        sample_rate_hertz: Audio sample rate in Hz
        language_code: Language code for transcription
        enable_automatic_punctuation: Add punctuation to transcription
        model: Speech model to use ("phone_call" recommended for voice calls)
        
    Returns:
        Transcribed text or None if transcription fails
    """
    from flask import current_app
    
    try:
        credentials = _get_speech_credentials(current_app.config)
        client = speech.SpeechClient(credentials=credentials)
        
        config = RecognitionConfig(
            encoding=RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate_hertz,
            language_code=language_code,
            enable_automatic_punctuation=enable_automatic_punctuation,
            model=model,
        )
        
        audio = RecognitionAudio(content=audio_content)
        
        log.info("Transcribing audio with Google Speech-to-Text")
        response = client.recognize(config=config, audio=audio)
        
        # Combine all alternatives into a single transcript
        transcripts = []
        for result in response.results:
            if result.alternatives:
                transcripts.append(result.alternatives[0].transcript)
        
        full_transcript = " ".join(transcripts)
        log.info("Transcription complete: %r", full_transcript)
        return full_transcript if full_transcript else None
        
    except Exception as e:
        log.exception("Google Speech-to-Text transcription failed: %s", e)
        return None


def save_audio_temporarily(audio_content: bytes, prefix: str = "audio") -> str:
    """
    Save audio content to a temporary file.
    
    Args:
        audio_content: Raw audio bytes
        prefix: Prefix for the temporary filename
        
    Returns:
        Path to the temporary audio file
    """
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=".wav")
    try:
        os.write(fd, audio_content)
        os.close(fd)
        log.debug("Saved temporary audio file: %s", path)
        return path
    except Exception as e:
        log.error("Failed to save temporary audio file: %s", e)
        try:
            os.close(fd)
            os.unlink(path)
        except:
            pass
        raise


def convert_audio_format(
    input_path: str,
    output_path: str,
    target_sample_rate: int = 16000,
    target_channels: int = 1,
) -> bool:
    """
    Convert audio file to a different format.
    
    Requires ffmpeg to be installed on the system.
    
    Args:
        input_path: Path to input audio file
        output_path: Path to output audio file
        target_sample_rate: Target sample rate in Hz (16000 recommended for STT)
        target_channels: Target number of channels (1 for mono)
        
    Returns:
        True if conversion successful, False otherwise
    """
    import subprocess
    
    try:
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ar", str(target_sample_rate),
            "-ac", str(target_channels),
            "-y",  # Overwrite output file
            output_path,
        ]
        log.debug("Converting audio: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            log.error("FFmpeg conversion failed: %s", result.stderr)
            return False
        
        log.info("Audio conversion successful: %s", output_path)
        return True
        
    except subprocess.TimeoutExpired:
        log.error("Audio conversion timed out")
        return False
    except FileNotFoundError:
        log.error("FFmpeg not found - install ffmpeg to enable audio conversion")
        return False
    except Exception as e:
        log.exception("Audio conversion failed: %s", e)
        return False


def validate_audio_format(audio_content: bytes) -> dict:
    """
    Validate audio content format.
    
    Args:
        audio_content: Raw audio bytes
        
    Returns:
        Dict with format information:
        {
            "valid": bool,
            "format": str | None,
            "sample_rate": int | None,
            "channels": int | None,
            "duration_seconds": float | None,
        }
    """
    import wave
    import io
    
    result = {
        "valid": False,
        "format": None,
        "sample_rate": None,
        "channels": None,
        "duration_seconds": None,
    }
    
    try:
        with wave.open(io.BytesIO(audio_content), "rb") as wav_file:
            result["valid"] = True
            result["format"] = "WAV"
            result["sample_rate"] = wav_file.getframerate()
            result["channels"] = wav_file.getnchannels()
            frames = wav_file.getnframes()
            result["duration_seconds"] = frames / result["sample_rate"]
    except Exception as e:
        log.debug("Audio validation failed: %s", e)
        result["format"] = "unknown"
    
    return result
