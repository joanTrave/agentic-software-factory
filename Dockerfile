# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.5.14 AS uv

FROM python:3.12-slim AS builder

COPY --from=uv /uv /uvx /usr/local/bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --all-groups

FROM python:3.12-slim AS final

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini entrypoint.sh gunicorn.conf.py pyproject.toml ./
COPY templates/ templates/
COPY translations/ translations/
COPY tests/ tests/

RUN adduser --system --group appuser \
    && chmod +x entrypoint.sh \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
