# customers-talking — monorepo task runner
# Usage: just <command>

default:
    @just --list

# Install all dependencies and copy .env if missing
install:
    cd server && uv sync
    cd client && npm install
    @test -f server/.env || (cp server/.env.example server/.env && echo "✓ Created server/.env — fill in your credentials.")

# Start Flask + Angular dev servers concurrently
dev:
    #!/usr/bin/env bash
    trap 'kill 0' EXIT
    (cd server && uv run flask --app main run --debug --port 5000) &
    (cd client && ng serve --open) &
    wait

# Build the Angular client for production
build:
    cd client && ng build --configuration production
