# Voice API Integration Guide

This guide explains how the Voice API integrates with Dialogflow CX to enable natural voice conversations with your AI agent.

## Overview

The Voice API now supports:
- **Speech-to-Text (STT)**: Transcribe caller speech using Google Cloud Speech-to-Text
- **Intent Detection**: Send transcribed text (or raw audio) to Dialogflow CX for intent recognition
- **Natural Conversations**: Allow callers to speak naturally instead of pressing DTMF keys
- **Escalation**: Automatically transfer to human agents when needed

## Architecture

```
Caller → Africa's Talking → Flask Voice Webhook
                              ↓
                      Download Audio Recording
                              ↓
                  Google Speech-to-Text (transcribe)
                              ↓
                    Dialogflow CX (detect intent)
                              ↓
                      VoiceXML Response (TTS)
                              ↓
                        Caller hears response
```

## Setup

### 1. Enable Google Cloud APIs

Ensure the following APIs are enabled in your Google Cloud project:

```bash
gcloud services enable dialogflow.googleapis.com
gcloud services enable speech.googleapis.com
```

### 2. Configure Environment Variables

Update your `server/.env` file with the following voice-specific variables:

```bash
# Voice Configuration
VOICE_SAMPLE_RATE_HZ=16000          # Audio sample rate (16kHz recommended)
VOICE_LANGUAGE_CODE=en-US           # Language for speech recognition
VOICE_ENABLE_RECORDING=true         # Enable call recording
VOICE_RECORDING_STORAGE_URL=        # Optional: GCS bucket for recordings

# Dialogflow CX (required)
DIALOGFLOW_PROJECT_ID=your-project-id
DIALOGFLOW_LOCATION=global
DIALOGFLOW_AGENT_ID=your-agent-uuid
DIALOGFLOW_LANGUAGE_CODE=en

# Google Service Account (required for Speech-to-Text & Dialogflow)
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-sa@your-project.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY_ID=your-key-id
GOOGLE_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
```

### 3. Install Dependencies

```bash
cd server
pip install -r pyproject.toml
# Or with uv:
uv pip install -r pyproject.toml
```

### 4. Configure Africa's Talking

Set up your Africa's Talking voice application:

1. Go to [Africa's Talking Dashboard](https://africastalking.com/)
2. Navigate to **Voice → Settings**
3. Set **Voice Callback URL** to: `https://your-server.com/voice`
4. Enable **Call Recording** (optional)
5. Set **Recording Callback URL** to: `https://your-server.com/voice/callback`

## Usage

### Endpoint: `/voice` (POST)

Main voice webhook endpoint that handles:
- Initial call greeting
- DTMF input (fallback)
- Voice recording callbacks

**Request Parameters:**
- `callerNumber`: Caller's phone number
- `sessionId`: Unique session identifier
- `dtmfDigits`: DTMF keypad input (if any)
- `recordingUrl`: URL to recorded audio (if recording enabled)

**Response:** VoiceXML format

### Endpoint: `/voice/callback` (POST)

Dedicated callback for processing voice recordings.

**Request Parameters:**
- `recordingUrl`: Public URL to the recorded audio
- `sessionId`: Session identifier
- `callerNumber`: Caller's phone number

**Flow:**
1. Downloads audio from `recordingUrl`
2. Sends audio to Dialogflow CX for speech recognition
3. Dialogflow returns transcribed text + intent + response
4. Returns VoiceXML with bot's spoken response

## Dialogflow CX Agent Configuration

### Required Intents

Create intents in your Dialogflow CX agent for common queries:

1. **Order Status**: "Where is my order?", "Check order status"
2. **Account Help**: "I need help with my account", "Reset password"
3. **Live Agent Handoff**: "Speak to agent", "Human support"

### Live Agent Handoff

To enable escalation to human agents:

1. In Dialogflow CX, create a route that triggers `live_agent_handoff`
2. Add metadata with `reason` field
3. The bot will transfer the call and mark session as "escalated"

Example handoff response in Dialogflow:
```json
{
  "payload": {
    "live_agent_handoff": {
      "metadata": {
        "reason": "Customer requested human agent"
      }
    }
  }
}
```

## Testing

### Local Testing

1. Start the Flask server:
```bash
cd server
python main.py
```

2. Use ngrok to expose your local server:
```bash
ngrok http 5000
```

3. Update Africa's Talking callback URL to use ngrok URL

### Test Voice Recording Flow

1. Call your Africa's Talking number
2. Speak your query when prompted
3. Africa's Talking records and sends to `/voice/callback`
4. Check server logs for transcription and Dialogflow response

### Verify Logs

```bash
# Check transcription
INFO: Transcribed voice input: "I want to check my order status"

# Check Dialogflow response
INFO: Dialogflow intent=order.status handoff=False
```

## Troubleshooting

### "Missing Google credentials" Error

Ensure all Google Service Account environment variables are set correctly:
- `GOOGLE_SERVICE_ACCOUNT_EMAIL`
- `GOOGLE_PRIVATE_KEY` (with `\n` for newlines)
- `GOOGLE_PRIVATE_KEY_ID`

### Speech-to-Text Fails

1. Verify Speech-to-Text API is enabled
2. Check service account has `Speech-to-Text User` role
3. Ensure audio format is WAV with correct sample rate (16kHz)

### Dialogflow Returns Fallback

1. Verify Dialogflow agent ID is a valid UUID
2. Check agent is published and has training phrases
3. Ensure language codes match between config and agent

### Audio Quality Issues

- Use 16kHz sample rate for telephony audio
- Ensure mono (single channel) audio
- Consider noise reduction if background noise is high

## Advanced Features

### Multi-language Support

Set `VOICE_LANGUAGE_CODE` to support different languages:
```bash
VOICE_LANGUAGE_CODE=es-ES    # Spanish
VOICE_LANGUAGE_CODE=fr-FR    # French
VOICE_LANGUAGE_CODE=sw-KE    # Swahili
```

### Custom Speech Models

For domain-specific terminology, use Cloud Speech-to-Text with custom classes or phrase sets.

### Real-time Streaming

For real-time streaming (not just recordings), consider:
- Dialogflow CX Telephony integration
- WebRTC for browser-based voice
- Twilio Media Streams for real-time audio

## Security

- All audio is processed temporarily and not stored permanently
- Service account credentials should be stored in Secret Manager in production
- Enable CDR (Call Detail Records) logging for audit trails

## Performance

- Average transcription latency: 1-3 seconds
- Dialogflow intent detection: < 500ms
- Total response time: 2-5 seconds (depending on audio length)

## Next Steps

1. Set up Dialogflow CX agent with your business intents
2. Configure Africa's Talking voice application
3. Test with sample calls
4. Monitor logs and refine intents
5. Deploy to production (Cloud Run recommended)
