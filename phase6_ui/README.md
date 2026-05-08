# Phase 6 — Pulse UI (Next.js)

Modern **Gen‑Z** dashboard: neon gradients, glass cards, Syne + DM Sans typography.

## Routes

| Path | What |
|------|------|
| `/` | Latest pulse + controls (generate demo run, send email via local Python) |
| `/history` | Archive of run IDs |
| `/history/[runId]` | Read-only pulse |
| `/runs/[runId]` | Simulated pipeline progress (until cloud worker lands) |

## Run locally

From repo root:

```bash
cd phase6_ui
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) (or the port Next prints if 3000 is busy).

### If you see a **404**

1. Use **`/`** or **`/history`** — other paths show the branded 404 until they exist.
2. Run the dev server from **`phase6_ui`** (`npm run dev`) so `../data/output` resolves correctly.
3. On **Vercel**, set **Root Directory** to **`phase6_ui`** (not the monorepo root), or the App Router won’t match.

Pulse data is read from `../data/output/pulse_*.json` when present; otherwise from `public/sample/`.

## Pipeline & email

- **`Fetch latest data & send email`** — Runs **phases 1–4** (ingest → pulse), then **phase 5** (draft/send). Uses **`data/cache/session.json`** so that the **same week range** can **reuse** the last successful pulse for **24 hours** (shared cache — fine for one Groww dataset). Check **Force fresh run** to always pull new reviews and rebuild before sending.
- **`Generate pulse only`** — Runs phases **1–4** via `python -m orchestrator.run_pipeline` (no email).

Requires repo-root **`.env`**: `GROQ_API_KEY`, plus SMTP or Resend for send. Full pipeline can take **several minutes** locally.

Disabled on Vercel (`501`) until a hosted worker exists.

## Deploy (Vercel)

Connect the `phase6_ui` folder as the project root. Static pages work; live pipeline + email need the Python worker described in `architecture.md`.
