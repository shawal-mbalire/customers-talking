FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY server/pyproject.toml server/uv.lock* ./
RUN uv sync --frozen --no-dev
COPY server/ .
# PORT is injected by Cloud Run (default 8080); use shell form so $PORT expands
CMD uv run gunicorn main:app --bind "0.0.0.0:${PORT:-8080}" --workers 2
