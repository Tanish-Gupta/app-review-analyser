# Groww Play Store — Weekly Pulse

Turn the last 12+ weeks of Groww's Play Store reviews into a one-page weekly pulse
(Top 3 themes · 3 user quotes · 3 action ideas) and a drafted email — viewable in
a Vercel-hosted Next.js UI.

> Full architecture is documented in [`architecture.md`](./architecture.md).

## Status

| Phase | What it does | Status |
|---|---|---|
| 1 — Ingest | Pull Play Store reviews (≥ 12 weeks) | ✅ built |
| 2 — Clean + PII scrub | Dedupe, lang filter, mask PII | ✅ built |
| 3 — Theme discovery & grouping | Groq-powered theming | ✅ built |
| 4 — Pulse builder | Render the one-pager | ✅ built |
| 5 — Email | Draft / send via Resend or SMTP | ✅ built |
| 6 — Vercel UI | Next.js dashboard ([deploy + Railway wiring](./phase6_ui/README.md#connect-vercel-to-railway)) | ✅ UI; pipeline on **Railway** when env set |

## Quick start (Phase 1 only, today)

```bash
# 1. Set up a virtualenv (Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# 2. Install Phase 1 deps
pip install -r requirements.txt

# 3. Copy env and edit if needed
cp .env.example .env

# 4. Run Phase 1 — fetch Groww reviews from the last 12 weeks
python -m phase1_ingest.run --weeks 12
```

You should see a per-rating histogram and a path to
`data/raw/raw_reviews_<run_id>.json`.

## Layout

```
app review analyser/
├── architecture.md        # full design doc
├── config/                # central settings (pydantic-settings)
├── phase1_ingest/         # ✅ Play Store scraper
├── phase2_clean/          # PII scrub, dedupe, language filter
├── phase3_themes/         # Groq theme discovery + classification
├── phase4_pulse/          # one-pager builder
├── phase5_email/          # email draft / send
├── phase6_ui/             # Next.js UI (Vercel; proxies to Railway when env set)
├── railway_api/           # FastAPI + Dockerfile for Railway (pipeline over HTTP)
├── orchestrator/          # CLI + run_all() pipeline
├── data/                  # local artefacts (gitignored)
└── tests/
```

## Railway (Docker API)

The pipeline runs in **`railway_api`** (`Dockerfile` at repo root). See **[railway_api/README.md](./railway_api/README.md)**.

1. Create a Railway service from this repo; **Dockerfile** build (root directory `.`).
2. Set **`RAILWAY_API_SECRET`**, **`GROQ_API_KEY`**, **`PLAYSTORE_APP_ID`**, and email vars (**`EMAIL_FROM`**, SMTP or **`RESEND_API_KEY`**).
3. On **Vercel** (Phase 6 project), add **`RAILWAY_API_URL`** and **`RAILWAY_API_SECRET`** — see **[`phase6_ui/.env.example`](./phase6_ui/.env.example)** — then redeploy. Same secret string must exist on **Railway**.
