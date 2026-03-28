# ── Stage 1: Build Angular frontend ──────────────────────────────────────────
FROM node:22-slim AS frontend
WORKDIR /client
COPY client/package*.json ./
RUN npm ci
COPY client/ .
# env.js is gitignored; copy the example so Angular build has it
RUN cp public/env.example.js public/env.js
RUN npm run build

# ── Stage 2: Python / Flask server ───────────────────────────────────────────
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY server/pyproject.toml server/uv.lock* ./
RUN uv sync --frozen --no-dev
COPY server/ .

# Copy Angular build output into Flask's static folder
COPY --from=frontend /client/dist/client/browser ./static/

# Entrypoint injects runtime env vars into static/env.js before gunicorn starts
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# PORT is injected by Cloud Run (default 8080); use shell form so $PORT expands
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["sh", "-c", "uv run gunicorn main:app --bind 0.0.0.0:${PORT:-8080} --workers 2"]
