# customers-talking — monorepo task runner
# Usage: just <command>
#
# Deploy vars — override via env or inline: GCP_PROJECT=my-proj just deploy-api
gcp_project := env_var_or_default("GCP_PROJECT", "your-gcp-project-id")
gcp_region  := env_var_or_default("GCP_REGION",  "us-central1")

default:
    @just --list

# Install all dependencies and copy .env if missing
install:
    cd server && uv sync
    cd client && bun install && bun pm trust --all
    @test -f server/.env || (cp .env.example server/.env && echo "Created server/.env — fill in your credentials.")

# Start Flask + Tailwind watch + Angular dev servers (frees ports 5000 & 4200 first)
dev:
    #!/usr/bin/env bash
    for port in 5000 4200; do
        pids=$(lsof -ti:$port 2>/dev/null || true)
        [ -n "$pids" ] && echo "Killing PID(s) $pids on :$port" && echo "$pids" | xargs kill -9 2>/dev/null || true
    done
    trap 'kill 0' EXIT
    (cd server && uv run flask --app main run --debug --port 5000) &
    (cd client && bunx tailwindcss -i src/styles.css -o src/generated.css --watch --minify) &
    sleep 2
    (cd client && bunx ng serve --port 4200 --open) &
    wait

# Build the Angular client (CSS compiled first, then Angular)
build:
    cd client && bunx tailwindcss -i src/styles.css -o src/generated.css --minify
    cd client && bunx ng build

# Deploy the Angular frontend to Firebase Hosting
deploy-ui: build
    firebase deploy --only hosting

# Deploy the Flask backend to Google Cloud Run
deploy-api:
    gcloud run deploy customers-talking-api \
        --source server/ \
        --region {{gcp_region}} \
        --project {{gcp_project}} \
        --allow-unauthenticated

# Deploy everything (frontend + backend)
deploy: deploy-api deploy-ui
