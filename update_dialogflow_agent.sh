#!/usr/bin/env bash
set -euo pipefail

# Helper script to update Dialogflow CX agent UUID in Secret Manager and Cloud Run.
# Usage: run in Cloud Shell or any machine with gcloud authenticated.

PROJECT="test-analytics-411507"
SERVICE="customers-talking-api"
REGION="europe-west1"
UUID="2c676234-651f-4d29-bb48-4d5d041a1b73"
SECRET_NAME="DIALOGFLOW_AGENT_ID"

echo "Project: $PROJECT, Service: $SERVICE, Region: $REGION"

echo "1) Ensure gcloud is available"
if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found. Run this script in Cloud Shell or install gcloud locally." >&2
  exit 1
fi

# Update or create secret
if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT" >/dev/null 2>&1; then
  echo "Adding new secret version with UUID..."
  echo -n "$UUID" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project="$PROJECT"
else
  echo "Creating secret and adding version..."
  echo -n "$UUID" | gcloud secrets create "$SECRET_NAME" --data-file=- --project="$PROJECT"
fi

# Update Cloud Run env var (forces a new revision)
echo "Updating Cloud Run service env var (this triggers a new revision)..."
gcloud run services update "$SERVICE" --region="$REGION" --project="$PROJECT" --update-env-vars=DIALOGFLOW_AGENT_ID="$UUID"

# Wait for revision to be ready (will print status)
echo "Waiting for service to become ready... (this may take a minute)"
gcloud run services describe "$SERVICE" --region="$REGION" --project="$PROJECT" --format="value(status.latestReadyRevisionName)"

# Quick verification
echo "----- Verify /debug/dialogflow (response below) -----"
curl -i "https://customerstalking-813431977200.$REGION.run.app/debug/dialogflow" || true

echo "Done. If /debug/dialogflow still returns 404 for 'customertalking', inspect Cloud Run revisions and secret mapping."

echo "Useful commands:"
echo "  gcloud run revisions list --service=$SERVICE --region=$REGION --project=$PROJECT"
echo "  gcloud run services describe $SERVICE --region=$REGION --project=$PROJECT --format='yaml(spec.template.spec.containers[0].env)'"

echo "If your Cloud Run was configured to use --update-secrets, ensure the secret name matches and Cloud Build used --update-secrets flag during deploy."
