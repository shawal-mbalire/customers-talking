FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY server/pyproject.toml server/uv.lock* ./
RUN uv sync --frozen --no-dev
COPY server/ .
ENV PORT=8080
CMD ["uv", "run", "gunicorn", "main:app", "--bind", "0.0.0.0:8080", "--workers", "2"]
