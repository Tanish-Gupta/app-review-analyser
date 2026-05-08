# Pulse pipeline API — Groq, Play Store ingest, email (Railway, Fly, etc.)
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PIP_NO_CACHE_DIR=1

COPY requirements-docker.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements-docker.txt

# Optional spaCy NER for PII masking (Phase 2); safe to skip if download fails
RUN python -m spacy download en_core_web_sm || true

COPY config ./config
COPY orchestrator ./orchestrator
COPY phase1_ingest ./phase1_ingest
COPY phase2_clean ./phase2_clean
COPY phase3_themes ./phase3_themes
COPY phase4_pulse ./phase4_pulse
COPY phase5_email ./phase5_email
COPY railway_api ./railway_api

RUN mkdir -p data/raw data/interim data/output data/cache

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn railway_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
