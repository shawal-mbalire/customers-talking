# Voice API Deployment Guide

This guide explains how to deploy the Voice API with Dialogflow integration to Google Cloud Run.

## What Changed

The Voice API now fully utilizes Dialogflow CX for:
- **Speech Recognition**: Transcribe caller speech using Google Cloud Speech-to-Text
- **Intent Detection**: Send audio directly to Dialogflow CX for natural language understanding
- **AI Responses**: Get intelligent responses from your Dialogflow agent
- **Escalation**: Automatically transfer to human agents when needed

## Pre-Deployment Checklist

### 1. Enable Required Google Cloud APIs

Run these commands to enable the necessary APIs:

```bash
gcloud services enable dialogflow.googleapis.com
gcloud services enable speech.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
```

### 2. Verify Service Account Permissions

Your Google Service Account needs these roles:
- `Dialogflow API Admin`
- `Cloud Speech-to-Text User`
- `Cloud Run Invoker`

Check and grant permissions:

```bash
# Get your service account email
gcloud iam service-accounts list

# Grant Dialogflow Admin role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/dialogflow.admin"

# Grant Speech-to-Text User role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/cloudspeech.user"
```

### 3. Verify Dialogflow CX Agent

Ensure your Dialogflow CX agent is properly configured:

1. Go to [Dialogflow CX Console](https://console.cloud.google.com/dialogflow/cx)
2. Select your agent: `adg-internal-tech-sandbox`
3. Verify the agent ID: `2c676234-651f-4d29-bb48-4d5d041a1b73`
4. Ensure intents are trained with sample phrases
5. Test the agent in the Dialogflow simulator

### 4. Configure Africa's Talking

Set up voice callbacks:

1. Login to [Africa's Talking Dashboard](https://africastalking.com/)
2. Go to **Voice → Settings**
3. Set **Callback URL** to: `https://your-cloud-run-url/voice`
4. Enable **Call Recording** (recommended)
5. Set **Recording Callback URL** to: `https://your-cloud-run-url/voice/callback`

## Deployment Steps

### Option 1: Push to GitHub (Automatic)

The app is configured for automatic deployment via Cloud Build:

```bash
# Make your changes
git add .
git commit -m "feat: enable voice API with Dialogflow integration"
git push origin main
```

Cloud Build will automatically:
1. Build the Docker image with new dependencies
2. Push to Artifact Registry
3. Deploy to Cloud Run with updated environment variables

### Option 2: Manual Deploy

```bash
cd /home/shawal/GitHub/customersTalking

# Build and deploy
gcloud builds submit --config cloudbuild.yaml \
  --substitutions _SERVICE_NAME=customers-talking-api,_REGION=europe-west1
```

## Environment Variables

The following environment variables are injected by Cloud Build:

### Dialogflow CX
```
DIALOGFLOW_PROJECT_ID=adg-internal-tech-sandbox
DIALOGFLOW_LOCATION=global
DIALOGFLOW_AGENT_ID=2c676234-651f-4d29-bb48-4d5d041a1b73
DIALOGFLOW_LANGUAGE_CODE=en
```

### Voice Configuration (NEW)
```
VOICE_SAMPLE_RATE_HZ=16000
VOICE_LANGUAGE_CODE=en-US
VOICE_ENABLE_RECORDING=true
```

### Google Service Account (Secrets)
```
GOOGLE_SERVICE_ACCOUNT_EMAIL
GOOGLE_PRIVATE_KEY
GOOGLE_PRIVATE_KEY_ID
```

## Verify Deployment

### 1. Check Cloud Run Service

```bash
gcloud run services describe customers-talking-api --region europe-west1
```

### 2. Check Environment Variables

```bash
gcloud run services describe customers-talking-api \
  --region europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"
```

### 3. Test Health Endpoint

```bash
SERVICE_URL=$(gcloud run services describe customers-talking-api \
  --region europe-west1 \
  --format="value(status.url)")

curl $SERVICE_URL/health
```

### 4. Test Voice Endpoint

```bash
# Simulate Africa's Talking callback
curl -X POST $SERVICE_URL/voice \
  -d "callerNumber=+254700000000" \
  -d "sessionId=test-session-123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Expected response (VoiceXML):
```xml
<?xml version="1.0"?>
<Response>
  <GetDigits timeout="30" finishOnKey="#" callbackUrl="...">
    <Say>Welcome to Customer Care...</Say>
  </GetDigits>
</Response>
```

### 5. Check Logs

```bash
gcloud run services logs read customers-talking-api --region europe-west1 --limit 50
```

Look for:
- `Transcribed voice input: ...`
- `Dialogflow intent=...`
- `Dialogflow CX audio call`

## Testing Voice Calls

### Test Call Flow

1. **Dial your Africa's Talking number**
2. **Listen to the greeting**: "Welcome to Customer Care..."
3. **Speak your query** (if recording enabled) or **press DTMF keys**
4. **Wait for AI response** from Dialogflow
5. **Continue conversation** or **press 0 to hang up**

### Expected Behavior

| User Input | Dialogflow Intent | Bot Response |
|------------|------------------|--------------|
| "1" (DTMF) | order.status | "Your order is being processed..." |
| "Where is my order?" (voice) | order.status | "Your order is being processed..." |
| "2" (DTMF) | account.help | "I can help with your account..." |
| "I need help with my account" (voice) | account.help | "I can help with your account..." |
| "Speak to agent" (voice) | live_agent_handoff | "Transferring you to a specialist..." |

## Troubleshooting

### Build Fails

Check Cloud Build logs:
```bash
gcloud builds list --limit 5
gcloud builds log BUILD_ID
```

Common issues:
- Missing `google-cloud-speech` in pyproject.toml ✓ Fixed
- Python syntax errors ✓ Verified with py_compile

### Runtime Errors

Check Cloud Run logs:
```bash
gcloud run services logs read customers-talking-api \
  --region europe-west1 \
  --filter "severity=ERROR" \
  --limit 20
```

### "Missing Google credentials"

Ensure secrets are properly set in Secret Manager:
```bash
gcloud secrets list
gcloud secrets versions access latest --secret=GOOGLE_PRIVATE_KEY
```

### "Dialogflow agent not found"

Verify agent ID is correct:
```bash
gcloud dialogflow agents list --project=adg-internal-tech-sandbox
```

### Voice Recording Not Working

1. Ensure Africa's Talking has recording enabled
2. Check `VOICE_ENABLE_RECORDING=true` in Cloud Run
3. Verify recording URL is accessible

## Rollback

If something goes wrong, rollback to previous version:

```bash
# List revisions
gcloud run revisions list --service=customers-talking-api --region=europe-west1

# Rollback
gcloud run services update-traffic customers-talking-api \
  --region=europe-west1 \
  --to-revisions=REVISION_NAME=100
```

## Post-Deployment

### Monitor Usage

```bash
# View request count
gcloud monitoring metrics list --filter='resource.type="cloud_run_revision"'

# View latency
gcloud run services describe customers-talking-api --region=europe-west1 \
  --format="value(status.latestCreatedRevisionUrl)"
```

### Set Up Alerts

Create monitoring alerts for:
- High error rate (> 5%)
- High latency (> 5 seconds)
- Dialogflow API quota usage

## Next Steps

1. ✅ Deploy to Cloud Run
2. ✅ Test with real phone calls
3. ✅ Monitor logs and fix any issues
4. ✅ Refine Dialogflow intents based on user queries
5. ✅ Set up monitoring and alerts

## Support

For issues:
- Check logs: `gcloud run services logs read customers-talking-api`
- Test Dialogflow: [Dialogflow Simulator](https://console.cloud.google.com/dialogflow/cx)
- Africa's Talking docs: https://docs.africastalking.com/voice
