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

## Connect Vercel to Railway

If **`RAILWAY_API_URL`** and **`RAILWAY_API_SECRET`** are set on **Vercel**, **`/api/run`**, **`/api/generate-pulse`** (same handler), and **`/api/email`** proxy to your **Railway** FastAPI service — **Generate pulse** and **Fetch & send** work from the hosted UI. Groq and email credentials live on **Railway**, not Vercel.

See **[`phase6_ui/.env.example`](./.env.example)** for copy-paste names and **[`railway_api/README.md`](../railway_api/README.md)** for the HTTP API.

Without those env vars on Vercel, those buttons return **501** (no local Python on Vercel).

**Timeouts:** The full pipeline can run **many minutes** on Railway. **Vercel Hobby** serverless functions are capped at **~10 seconds** — the request will die with no success. Use **Vercel Pro** (or run the UI locally) so `/api/email` can use **`maxDuration` = 300s** (already set on the route). For runs longer than 5 minutes, you still need a **async job** architecture later.

## Deploy (Vercel)

**Yes — deploy the Next.js app.** Vercel runs **Phase 6** in the browser and as serverless routes. The Python pipeline runs **on Railway** when `RAILWAY_API_URL` + `RAILWAY_API_SECRET` are set; otherwise it runs only **locally** via `python3`.

### Steps

1. Push this repo to GitHub (you already have [Tanish-Gupta/app-review-analyser](https://github.com/Tanish-Gupta/app-review-analyser)).
2. In [Vercel](https://vercel.com/new) → **Add New Project** → import that repo.
3. **Critical:** under **Configure Project**, set **Framework Preset** to **Next.js** (not Python).
4. **Root Directory:** set to **`phase6_ui`** (recommended). Then clear **Output Directory** in Vercel **Settings → General** (leave empty). Do **not** combine “Root = `phase6_ui`” with **`outputDirectory: phase6_ui/.next`** — that doubles the path to `phase6_ui/phase6_ui/.next`.
5. If you instead leave **Root Directory** at **`.`** (repo root), set **Output Directory** in the Vercel dashboard to **`phase6_ui/.next`** (the root `vercel.json` no longer sets it, to avoid the duplicate-path bug).
6. Either:
   - With **Root = `phase6_ui`:** use default **Install** `npm install` and **Build** `npm run build`, **or**
   - With **Root = `.`:** the root **`vercel.json`** runs **`npm install`** + **`npm run build`** at the repo root (workspaces).
7. Add **Environment variables** (see **`.env.example`** in this folder): at minimum **`RAILWAY_API_URL`** + **`RAILWAY_API_SECRET`** to use your Railway backend.
8. Deploy. The site will show **`public/sample/`** pulse data when `data/output/` is absent (normal on Vercel); after a successful Railway-backed run, refresh — **note:** new pulse JSON still lands on Railway’s disk, not Vercel’s filesystem, so the **home page** may keep showing **sample** until you add blob sync or copy artifacts into **`public/sample/`** (see architecture doc).

### “No python entrypoint found”

Vercel saw **`requirements.txt`** at the repo root and assumed a **Python** project. Fix: use **Next.js** as the framework and either **Root Directory = `phase6_ui`** or pull the latest repo (root **`vercel.json`** + **`package.json`** delegates the build to the UI folder).

### “No Next.js version detected”

Vercel reads the **`package.json` in your Root Directory**. If Root Directory is **`.`** (repo root), that file must list **`next`** in **dependencies** — the monorepo root **`package.json`** now does, plus **`workspaces`: [`phase6_ui`]**. Alternatively set **Root Directory** to **`phase6_ui`** only so Vercel reads **`phase6_ui/package.json`** directly.

### “The Next.js output directory `.next` was not found” / `phase6_ui/phase6_ui/.next`

- **Cause:** **Root Directory** is **`phase6_ui`** but **Output Directory** was set to **`phase6_ui/.next`** (e.g. from root `vercel.json`). Vercel resolves that **under** `phase6_ui`, so the path doubles.
- **Fix:** Use **Root Directory = `phase6_ui`** and leave **Output Directory** **empty** (default `.next` next to `package.json`). Or use **Root = `.`** and set dashboard **Output Directory** to **`phase6_ui/.next`** only in that case.

### What works where

| Where | UI | Pipeline + email |
|-------|----|------------------|
| **Local** (`npm run dev` in `phase6_ui`) | Yes | Local `python3` if Railway env **not** set; else **Railway** |
| **Vercel** | Yes | **Railway** only if `RAILWAY_API_URL` + `RAILWAY_API_SECRET` set; else **501** |

### Showing your own pulse on production

- **Quick:** Copy built artifacts into `phase6_ui/public/sample/` (`pulse.json`, `.md`, `.html`) and redeploy, **or**
- **Proper:** Store pulses in blob storage (e.g. Vercel Blob) and teach `lib/pulses.ts` to read from URL — not implemented yet; see `architecture.md` for a worker-based design.
