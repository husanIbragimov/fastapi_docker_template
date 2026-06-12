# syntax=docker/dockerfile:1
FROM python:3.13-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY ../pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install \
        "fastapi[standard]>=0.115.0" \
        "sqlalchemy[asyncio]>=2.0.0" \
        "asyncpg>=0.30.0" \
        "alembic>=1.14.0" \
        "redis>=5.2.0" \
        "pydantic>=2.10.0" \
        "pydantic-settings>=2.7.0" \
        "pydantic[email]>=2.10.0" \
        "PyJWT>=2.10.0" \
        "bcrypt>=4.2.0" \
        "uvicorn[standard]>=0.34.0" \
        "python-multipart>=0.0.20" \
        "arq>=0.26.0" \
        "structlog>=24.4.0"

# ── Runtime ─────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY .. .

RUN chmod +x scripts/*.sh

EXPOSE 8000

CMD ["scripts/start.sh"]
