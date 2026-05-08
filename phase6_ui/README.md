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

**Yes — deploy the Next.js app.** Vercel runs **Phase 6 only**. The Python ingest → Groq → pulse pipeline does **not** run on Vercel’s serverless runtime (no bundled Python deps, long jobs, Play Store scrape). Those API routes return **501** with a clear message; run the pipeline **locally** (or on a separate worker) and ship pulses another way (see below).

### Steps

1. Push this repo to GitHub (you already have [Tanish-Gupta/app-review-analyser](https://github.com/Tanish-Gupta/app-review-analyser)).
2. In [Vercel](https://vercel.com/new) → **Add New Project** → import that repo.
3. **Critical:** under **Configure Project**, set **Framework Preset** to **Next.js** (not Python).
4. Either:
   - **Recommended:** set **Root Directory** to **`phase6_ui`**, then use default **Install Command** `npm install` and **Build Command** `npm run build`, **or**
   - Leave root directory as **`.`** — the monorepo root **`package.json`** declares **`next`** (and npm **workspaces** include `phase6_ui`) so Vercel detects Next.js; **`vercel.json`** runs **`npm install`** + **`npm run build`** at the repo root (still avoids Python owning the deploy because of top-level `requirements.txt`).
5. Deploy. The site will show **`public/sample/`** pulse data when `data/output/` is absent (normal on Vercel).

### “No python entrypoint found”

Vercel saw **`requirements.txt`** at the repo root and assumed a **Python** project. Fix: use **Next.js** as the framework and either **Root Directory = `phase6_ui`** or pull the latest repo (root **`vercel.json`** + **`package.json`** delegates the build to the UI folder).

### “No Next.js version detected”

Vercel reads the **`package.json` in your Root Directory**. If Root Directory is **`.`** (repo root), that file must list **`next`** in **dependencies** — the monorepo root **`package.json`** now does, plus **`workspaces`: [`phase6_ui`]**. Alternatively set **Root Directory** to **`phase6_ui`** only so Vercel reads **`phase6_ui/package.json`** directly.

### “The Next.js output directory `.next` was not found at …/path0/.next”

The app builds to **`phase6_ui/.next`**, not the repo root. The root **`vercel.json`** sets **`outputDirectory`** to **`phase6_ui/.next`**. In Vercel **Project → Settings → General**, clear any manual **Output Directory** override (leave empty / default) so **`vercel.json`** wins. Easiest alternative: set **Root Directory** to **`phase6_ui`** only and remove custom output directory — then `.next` lives next to that **`package.json`**.

### What works vs not

| On Vercel | Locally |
|-----------|---------|
| Dashboard UI, history, viewing **`public/sample`** pulses | Full pipeline + **`data/output`** pulses |
| **`Generate pulse` / `Fetch & send`** → **501** (by design) | Same buttons run Python + email |

### Showing your own pulse on production

- **Quick:** Copy built artifacts into `phase6_ui/public/sample/` (`pulse.json`, `.md`, `.html`) and redeploy, **or**
- **Proper:** Store pulses in blob storage (e.g. Vercel Blob) and teach `lib/pulses.ts` to read from URL — not implemented yet; see `architecture.md` for a worker-based design.
