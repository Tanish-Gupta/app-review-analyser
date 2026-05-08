# Railway / Docker API

FastAPI service wrapping `orchestrator.run_pipeline` and `phase5_email.run`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness (no auth) |
| POST | `/v1/pipeline/run` | Body: `{ "weeks": 12 }` — phases 1–4 |
| POST | `/v1/email` | Body: `weeks`, `recipient`, optional `recipientName`, `mode`, `forceRefresh` |

When `RAILWAY_API_SECRET` is set on the server, send:

`Authorization: Bearer <RAILWAY_API_SECRET>`

The Phase 6 Next.js app proxies here when **`RAILWAY_API_URL`** + **`RAILWAY_API_SECRET`** are set (e.g. on Vercel).

## Environment

Copy from repo `.env.example`: **`GROQ_API_KEY`**, Play Store **`PLAYSTORE_APP_ID`**, and email **`EMAIL_FROM`** / SMTP or **`RESEND_API_KEY`**.

Optional: **`CORS_ORIGINS`** (comma-separated; default `*`).

## Build & run locally

```bash
export PYTHONPATH="$(pwd)"
pip install -r requirements-docker.txt
export RAILWAY_API_SECRET=dev-secret
uvicorn railway_api.main:app --reload --port 8000
```

## Docker

From repo root:

```bash
docker build -t pulse-api .
docker run --rm -p 8000:8000 \
  -e RAILWAY_API_SECRET=test \
  -e GROQ_API_KEY=... \
  pulse-api
```

Railway sets **`PORT`** automatically; the image uses **`${PORT:-8000}`**.

## Railway dashboard (important)

If deploy fails with **`The executable 'npm' could not be found`**, Railway is still using **monorepo npm** commands from an earlier setup. This API image is **Python only** (no Node).

1. Open the service → **Settings**.
2. Under **Build** (or **Build & Deploy**): **delete / clear** **Custom Build Command** (remove `npm run build --workspace=...`). The **`Dockerfile`** must be the only build step.
3. Under **Deploy**: **delete / clear** **Custom Start Command** (remove `npm run start --workspace=...`). The container should start **`uvicorn`** (repo root **`railway.toml`** sets this; **`Dockerfile`** `CMD` matches).
4. Redeploy.

## Notes

- Container filesystem is ephemeral unless you attach a volume; `data/` is recreated each deploy.
- Full pipeline runs can exceed HTTP timeouts — consider background jobs for production scale.
