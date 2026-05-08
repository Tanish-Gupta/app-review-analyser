# Groww Play Store — Weekly Pulse Generator

**Phase-wise architecture document**
_Last updated: 2026-05-08_

---

## 1. Problem statement

Turn **at least the last 12 weeks** of Groww's Play Store reviews into a
**one-page weekly pulse** containing:

- Top 3 themes (LLM-discovered, then reviews grouped under them)
- 3 real user quotes (PII-scrubbed)
- 3 concrete action ideas
- A drafted email of the same note, sent to self / an alias
- A **web UI deployed on Vercel** that lets a user trigger a fresh run and view the rendered pulse

**Audience served**

| Team | Use of the pulse |
|---|---|
| Product / Growth | Decide what to fix next |
| Support | See & acknowledge what users are saying |
| Leadership | Quick weekly health check |

**Hard constraints**
- LLM provider: **Groq**
- **No PII** in any persisted output
- Review window: **≥ 12 weeks**
- Output: a one-page note + a draft email + a UI to view & regenerate it

---

## 2. High-level overview

```mermaid
flowchart LR
    subgraph Vercel
        UI[Phase 6<br/>Next.js UI]
        API[/api/run, /api/status,<br/>/api/pulse, /api/email,<br/>/api/cron/weekly<br/>Python serverless]
        BLOB[(Vercel Blob<br/>pulse.md/.html/.eml<br/>raw + interim)]
        KV[(Vercel KV<br/>run state + index)]
    end
    UI -->|POST /api/run| API
    UI -->|poll /api/status| API
    QS[Upstash QStash<br/>queue]
    API -->|enqueue job| QS
    QS -->|webhook| WORKER[/api/worker<br/>runs pipeline]
    WORKER --> B
    A[Play Store<br/>Groww app] -->|scrape| B(Phase 1<br/>Ingest)
    B --> C(Phase 2<br/>Clean + PII scrub)
    C --> D(Phase 3<br/>Theme discovery & classification<br/>Groq)
    D --> E(Phase 4<br/>Weekly pulse builder<br/>Groq for actions)
    E --> F(Phase 5<br/>Email draft & send)
    E --> BLOB
    WORKER --> KV
    F --> G[Inbox]
    BLOB -->|read| UI
    CRON[Vercel Cron<br/>Mon 09:00 IST] --> API
```

### Tech stack

| Concern | Choice |
|---|---|
| Language (pipeline) | Python 3.11 |
| Language (UI) | TypeScript / Next.js 14 (App Router) |
| Hosting | **Vercel** (single project, Next.js + Python serverless functions side-by-side) |
| UI styling | Tailwind CSS + shadcn/ui |
| Scraper | `google-play-scraper` (no auth, public reviews) |
| LLM | Groq API — `llama-3.1-70b-versatile` (reasoning), `llama-3.1-8b-instant` (cheap classification) |
| Embeddings (optional pre-cluster) | `sentence-transformers/all-MiniLM-L6-v2` (local, free) |
| Templating | Jinja2 (server-side) → Markdown rendered by `react-markdown` in the UI |
| Artifact storage | **Vercel Blob** (pulse `.md` / `.html` / `.eml`, raw + interim JSON) |
| Run state / progress | **Vercel KV** (Upstash Redis) keyed by `runId` |
| Job queue (long-running pipeline) | **Upstash QStash** webhook → `/api/worker` |
| Scheduling | **Vercel Cron** (weekly Mon 09:00 IST → `/api/cron/weekly`) |
| Email | **Resend** (Vercel-native HTTP API) — fallback: SMTP or `.eml` blob |
| Orchestration | Callable Python pipeline (`orchestrator/pipeline.py`) consumed by both the CLI and the serverless functions |
| PII NER | spaCy `en_core_web_sm` (loaded lazily inside the worker function) |

---

## 3. Repository layout

```
app review analyser/
├── README.md
├── architecture.md
├── requirements.txt
├── .env.example                 # GROQ_API_KEY, SMTP_*, ALERT_EMAIL
├── config/
│   └── settings.py              # central config (weeks_lookback=12 (min), app_id, ...)
├── phase1_ingest/
│   ├── README.md
│   └── src/
│       ├── playstore_scraper.py # google-play-scraper wrapper
│       └── models.py            # Review pydantic model
├── phase2_clean/
│   ├── README.md
│   └── src/
│       ├── pii_scrubber.py      # regex + spaCy NER
│       ├── deduplicate.py
│       └── language_filter.py
├── phase3_themes/
│   ├── README.md
│   └── src/
│       ├── groq_client.py       # thin Groq wrapper + retry/backoff
│       ├── theme_discovery.py   # generates 3–5 themes from sample
│       ├── theme_classifier.py  # assigns each review to a theme
│       └── prompts/
│           ├── discover_themes.txt
│           └── classify_review.txt
├── phase4_pulse/
│   ├── README.md
│   └── src/
│       ├── pulse_builder.py     # picks top themes + quotes
│       ├── action_generator.py  # Groq → 3 action ideas
│       └── templates/
│           ├── pulse.md.j2
│           └── pulse.html.j2
├── phase5_email/
│   ├── README.md
│   └── src/
│       ├── mailer_smtp.py       # SMTP fallback
│       ├── mailer_resend.py     # Resend HTTP API (default on Vercel)
│       └── eml_writer.py        # writes .eml to Blob/local
├── phase6_ui/                   # Next.js app (deployed to Vercel)
│   ├── README.md
│   ├── package.json
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # dashboard — latest pulse + Generate button
│   │   ├── history/
│   │   │   ├── page.tsx         # list of past pulses
│   │   │   └── [runId]/page.tsx # one historical pulse
│   │   └── globals.css
│   ├── components/
│   │   ├── PulseCard.tsx
│   │   ├── ThemeBars.tsx
│   │   ├── QuoteList.tsx
│   │   ├── ActionList.tsx
│   │   ├── RunProgress.tsx      # polls /api/run/[runId]/status
│   │   ├── ControlsBar.tsx      # weeks slider, email mode, run button
│   │   └── HistoryList.tsx
│   └── lib/
│       ├── api.ts               # typed fetch helpers
│       └── storage.ts           # signed URL helpers for Vercel Blob
├── api/                         # Vercel Python serverless functions
│   ├── run.py                   # POST  /api/run            → enqueue job
│   ├── status.py                # GET   /api/run/[runId]/status
│   ├── pulse.py                 # GET   /api/run/[runId]/pulse
│   ├── email.py                 # POST  /api/email/[runId]
│   ├── worker.py                # POST  /api/worker         (QStash webhook)
│   └── cron/
│       └── weekly.py            # GET   /api/cron/weekly    (Vercel Cron)
├── orchestrator/
│   ├── run_weekly.py            # end-to-end CLI (local)
│   └── pipeline.py              # importable functions — used by CLI **and** /api/worker
├── data/                        # local dev only — prod uses Vercel Blob
│   ├── raw/
│   ├── interim/
│   └── output/
├── vercel.json                  # routes, cron schedule, fn memory & maxDuration
├── requirements.txt             # Python deps for serverless functions
└── tests/
    └── test_*.py
```

---

## 4. Phase-by-phase architecture

### Phase 1 — Ingest

**Responsibility:** Pull **at least the last 12 weeks** of Play Store reviews for Groww and persist raw.

**Inputs**
- `app_id = "com.nextbillion.groww"` (configurable)
- `weeks_lookback = 12` (**minimum 12**, may be increased from the UI slider — capped at 26 to control runtime)
- Locale / country: `en` / `in`

**Library**
- `google-play-scraper` → `reviews_all(...)` with `Sort.NEWEST`, then date filter

**Schema (Review pydantic model)**

| Field | Type | Source |
|---|---|---|
| `review_id` | str | `reviewId` |
| `rating` | int (1–5) | `score` |
| `title` | str (rare on Play Store; default empty) | derived from first sentence |
| `text` | str | `content` |
| `date` | datetime | `at` |
| `app_version` | str \| null | `reviewCreatedVersion` |
| `helpful_count` | int | `thumbsUpCount` |

**Output:** `data/raw/raw_reviews_<run_id>.json` (~1k–5k rows typical).

**Failure modes / handling**
- Network errors → exponential backoff, max 3 retries
- Rate limit → sleep & resume; cache by `review_id`

---

### Phase 2 — Clean + PII scrub

**Responsibility:** Produce analysis-ready, PII-free reviews.

**Steps**
1. **Dedupe** by `review_id`, then near-dupe by normalized text hash.
2. **Language filter** — keep `en` (use `langdetect`); optionally translate `hi` → `en` later.
3. **Quality filter** — drop reviews with `len(text) < 15 chars`.
4. **PII scrubbing** (critical, brief says "Do NOT include PII"):
   - Regex: emails, phone numbers (Indian + intl), UPI handles (`@upi`), Aadhaar/PAN-shaped strings, account numbers ≥ 8 digits, URLs.
   - NER: spaCy `en_core_web_sm` → mask `PERSON` entities with `[USER]`.
   - Replace, don't delete (preserves grammar for the LLM).
5. **Normalization** — collapse whitespace; keep original case for quoting.

**Output:** `data/interim/clean_reviews_<run_id>.parquet`

**Why a separate phase:** keeps LLM calls in Phase 3 deterministic and cheap; the PII guarantee lives in one auditable place.

---

### Phase 3 — Theme discovery & grouping (Groq)

The heart of the system. Two-stage to keep cost + quality balanced.

#### Stage A — Theme discovery (one Groq call)
- Sample ~150 reviews **stratified by rating** (so negatives aren't drowned by 5-stars).
- Prompt Groq (`llama-3.1-70b-versatile`) to return **exactly 3–5 themes** as JSON:

  ```json
  [
    {
      "id": "T1",
      "name": "Order execution & glitches",
      "definition": "Issues with placing/cancelling orders, app crashes during market hours."
    }
  ]
  ```
- Response parsed with `pydantic`; retry on schema mismatch.

#### Stage B — Per-review classification
- For each clean review, call Groq (`llama-3.1-8b-instant`, cheap model) with the theme list and ask for a single best theme `id` + a 0–1 confidence.
- Batching: 20 reviews per request to cut tokens.
- **Optional speed-up:** pre-embed reviews + theme definitions with MiniLM, run cosine similarity to short-list 2 candidate themes, then let Groq pick — cuts LLM cost ~60%.

**Outputs**
- `data/interim/themes_<run_id>.json` — theme definitions
- `data/interim/themed_reviews_<run_id>.parquet` — every review with `theme_id`, `confidence`

**Aggregations computed here**
- Per theme: count, avg rating, % negative (≤2★), top 5 verbatim quotes (highest `helpful_count`, no PII).

---

### Phase 4 — Weekly pulse builder

**Responsibility:** Pick the headline themes and turn the data into a one-page note.

**Selection logic**
- **Top 3 themes** ranked by a composite score:
  ```
  score = volume_share * 0.5 + negative_share * 0.5
  ```
  (you care about big themes _and_ painful ones).
- **3 quotes**: one per top theme, picked by:
  1. Highest `helpful_count`
  2. Length 60–240 chars (readable)
  3. Already PII-clean
- **3 action ideas**: a single Groq call summarizing the 3 themes + their quotes → returns 3 concrete, prioritized actions tagged with owning team (Product / Eng / Support).

**Render**
- Jinja2 template → both `pulse.md` and `pulse.html`.
- One page, ≤ 350 words. Suggested layout:

  ```
  Groww Weekly Pulse — Week 19, 2026
  Reviews analyzed: 1,284  |  Avg rating: 3.6 ★  |  Window: Mar 1 – May 7

  Top themes
  1. <Theme A>  — 38% of reviews, 71% negative
  2. <Theme B>  — 22% of reviews, 30% negative
  3. <Theme C>  — 15% of reviews, 12% negative

  In their words
  • "<quote 1>"  (★2, May 3)
  • "<quote 2>"  (★1, May 5)
  • "<quote 3>"  (★4, May 6)

  Three things to do this week
  1. [Product] …
  2. [Eng]     …
  3. [Support] …
  ```

**Output:** `data/output/pulse_<YYYY-WW>.{md,html}`

---

### Phase 5 — Email draft & send

**Responsibility:** Deliver the note to the user's inbox.

**Two modes** (config switch `EMAIL_MODE`):

1. **`send`** — SMTP (Gmail App Password by default). HTML body = rendered `pulse.html`; plain-text fallback = `pulse.md`.
2. **`draft`** — write a `.eml` file (RFC 822) into `data/output/`. User can open it in any mail client and click send. Useful when no SMTP creds are configured (great for first run / submission).

**Fields**
- `From`: `ALERT_EMAIL`
- `To`: `ALERT_EMAIL` (self / alias)
- `Subject`: `Groww Weekly Pulse — Week {ISO_WEEK}, {YYYY}`
- Headers: `X-Generated-By: groww-pulse v0.1`

**Audit log:** append a row to `data/output/email_log.csv` (`run_id`, `timestamp`, `mode`, `status`).

---

### Phase 6 — Web UI (Next.js on Vercel)

**Responsibility:** A hosted web app where the user can (a) view the latest weekly pulse, (b) browse past pulses, (c) click "Generate" to kick off a fresh run, (d) draft / send the email — all from the browser, no terminal.

**Why Vercel + Next.js**
- Same provider for static UI **and** Python serverless functions (no separate API host).
- Built-in primitives: Vercel Cron (weekly schedule), Vercel Blob (artifact store), Vercel KV (run state), Vercel Functions (Python runtime).
- Free Hobby tier is enough for a portfolio/demo; Pro adds longer function timeouts.
- Fast global CDN for the rendered pulse, plus preview deploys per PR.

#### Frontend (Next.js App Router)

**Routes**

| Path | Purpose |
|---|---|
| `/` | Dashboard — shows the **latest** pulse + sticky `ControlsBar` |
| `/history` | List of past pulses (read from KV index) |
| `/history/[runId]` | One historical pulse (read-only) |
| `/runs/[runId]` | Live progress page after clicking Generate |

**Key components**
- `<ControlsBar />` — weeks slider (min 12, max 26), email mode (`draft`/`send`), recipient input, **Generate Weekly Pulse** button, **Send Email** button.
- `<PulseCard />` — header with run metadata (reviews analysed, avg rating, window).
- `<ThemeBars />` — Top 3 themes as horizontal bars (volume %, negative %).
- `<QuoteList />` — 3 quotes, each with rating + date badge.
- `<ActionList />` — 3 actions with team chip (`Product` / `Eng` / `Support`).
- `<RunProgress />` — polls `/api/run/[runId]/status` every 1.5s; shows phase 1/6 → 6/6 with a progress bar.
- `<HistoryList />` — paged table backed by Vercel KV `runs:index`.

**Mock screen layout**

```
┌──────────────────────────────────────────────────────────────────┐
│ Groww Weekly Pulse                          Latest · History · ⚙ │
├──────────────────────────────────────────────────────────────────┤
│ ControlsBar:  Weeks [▭▭▭▭▭ 12]   Mode [Draft|Send]   you@…       │
│               [ Generate Weekly Pulse ▶ ]   [ Send Email ✉ ]      │
├──────────────────────────────────────────────────────────────────┤
│ Reviews: 1,284   Avg: 3.6★   Window: Feb 13 – May 8              │
│                                                                  │
│ Top themes                In their words           Actions       │
│ ┌──────────────┐          ┌─────────────────┐    ┌────────────┐  │
│ │ Theme A 38% █│          │ "<quote 1>" ★2  │    │ 1 [Prod] … │  │
│ │ Theme B 22% █│          │ "<quote 2>" ★1  │    │ 2 [Eng]  … │  │
│ │ Theme C 15% █│          │ "<quote 3>" ★4  │    │ 3 [Supp] … │  │
│ └──────────────┘          └─────────────────┘    └────────────┘  │
│                                                                  │
│  ⬇ pulse.md     ⬇ pulse.html     ⬇ draft.eml                     │
└──────────────────────────────────────────────────────────────────┘
```

**Render**
- Next.js Server Components fetch the latest `pulse.json` (structured) from Vercel Blob; client components handle interactivity.
- Markdown bodies rendered with `react-markdown` + `remark-gfm`.

#### Backend (Python serverless functions in `api/`)

| Function | Method · Path | Job |
|---|---|---|
| `api/run.py` | `POST /api/run` | Validate input → mint `runId` → write `runs:{id}` to KV (status=`queued`) → enqueue QStash job → return `{ runId }` |
| `api/status.py` | `GET /api/run/[runId]/status` | Read KV `runs:{id}` → `{ status, phase, progress, error? }` |
| `api/pulse.py` | `GET /api/run/[runId]/pulse?fmt=md\|html\|json` | Stream the artifact from Blob (signed URL or proxy) |
| `api/email.py` | `POST /api/email/[runId]` | Send via Resend or write `.eml` to Blob |
| `api/worker.py` | `POST /api/worker` | **QStash webhook** — verifies signature, calls `pipeline.run_all(...)` with a KV-writing progress callback |
| `api/cron/weekly.py` | `GET /api/cron/weekly` | Hit by Vercel Cron Mon 09:00 IST → enqueues a run with default config |

**Why a queue (QStash)?**
- Vercel Hobby functions cap at **60 s**; Pro at **300 s**. Our pipeline targets < 3 min but can spike higher with cold-start + spaCy model load.
- `/api/run` returns immediately; QStash invokes `/api/worker` which has its own clock and supports retries/DLQ for free.
- For Pro users who want sync runs, a `?sync=1` query flag on `/api/run` runs in-process and skips QStash.

**Pipeline progress contract** — `pipeline.run_all` is updated to accept an `on_progress(phase: str, pct: float, meta: dict)` callback. The worker passes a callback that writes to Vercel KV:

```json
{
  "runId": "2026-W19-7f3a",
  "status": "running",
  "phase": "phase3_classify",
  "progress": 0.55,
  "started_at": "2026-05-08T11:31:02Z",
  "weeks": 12,
  "email_mode": "draft"
}
```

#### Storage layout (Vercel Blob)

```
blob://review-analyser/
├── runs/<runId>/raw_reviews.json
├── runs/<runId>/clean_reviews.parquet
├── runs/<runId>/themes.json
├── runs/<runId>/themed_reviews.parquet
├── runs/<runId>/pulse.md
├── runs/<runId>/pulse.html
├── runs/<runId>/pulse.json     # structured for the UI
└── runs/<runId>/email.eml      # only when email_mode=draft
```

#### Vercel KV keys

| Key | Value |
|---|---|
| `runs:index` | sorted set of `runId` by start time |
| `runs:{runId}` | JSON blob with status / phase / progress (above) |
| `runs:latest` | pointer to most recent successful `runId` |

#### `vercel.json` essentials

- `crons: [{ path: "/api/cron/weekly", schedule: "30 3 * * 1" }]`  (Mon 09:00 IST = 03:30 UTC)
- `functions: { "api/worker.py": { "maxDuration": 300, "memory": 1024 } }`
- Region pinned to `bom1` (Mumbai) for Play Store latency.

#### End-to-end "Generate" flow

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Next.js UI
    participant R as /api/run
    participant Q as QStash
    participant W as /api/worker
    participant K as Vercel KV
    participant B as Vercel Blob
    U->>UI: Click "Generate"
    UI->>R: POST /api/run {weeks, email_mode}
    R->>K: SET runs:{id} status=queued
    R->>Q: publish job(runId)
    R-->>UI: 202 {runId}
    UI->>UI: route to /runs/{runId}
    Q->>W: webhook /api/worker
    loop phases 1..6
        W->>K: SET runs:{id} phase=N progress=p
        UI->>R: GET /status (poll 1.5s)
        R-->>UI: {phase, progress}
    end
    W->>B: PUT pulse.{md,html,json,eml}
    W->>K: SET runs:{id} status=done; runs:latest={id}
    UI->>R: GET /pulse → render
```

**Failure handling**
- Worker exceptions → KV `status=error`, `error=<message>`, `phase=<which>` → UI shows an inline error card with a "Retry" button that posts to `/api/run` with `force=true`.
- QStash auto-retries the worker up to 3× with exponential backoff.

**Local dev**
- `next dev` for the UI on `:3000`.
- `vercel dev` runs both Next.js and the Python functions with the same routing as prod.
- Local Blob/KV are stubbed via filesystem (`data/`) and an in-memory dict, switched on by `RUN_LOCAL=1`.

---

## 5. Orchestrator

The orchestrator is split into two pieces so it can be driven by **the CLI, the cron, or the Vercel worker function**:

- `orchestrator/pipeline.py` — pure-Python, importable functions, **storage-backend agnostic**:
  ```python
  ingest(weeks: int, run_id: str, store: Storage) -> str       # blob key
  clean(run_id: str, store: Storage) -> str
  discover_themes(run_id: str, store: Storage) -> list[Theme]
  classify(run_id: str, store: Storage) -> str
  build_pulse(run_id: str, store: Storage) -> PulseArtifact
  email(run_id: str, mode: Literal["draft", "send"], store: Storage) -> EmailResult

  run_all(
      weeks: int,
      email_mode: str,
      store: Storage,                       # LocalFS or VercelBlob
      state: StateStore,                    # InMemory or VercelKV
      on_progress: Callable[[str, float, dict], None] | None = None,
  ) -> RunResult
  ```
  - `Storage` and `StateStore` are thin protocols; local dev uses filesystem + in-memory dict, prod uses Vercel Blob + Vercel KV.
  - `on_progress("phase3_classify", 0.55, {"batch": 7, "of": 12})` is what the worker writes to KV for the UI to poll.

- `orchestrator/run_weekly.py` — thin CLI wrapper around `run_all` with `LocalFS` + in-memory state:
  ```bash
  python -m orchestrator.run_weekly \
      --weeks 12 \
      --email-mode draft \
      --run-id auto
  ```

Each step is **idempotent** and keyed by `run_id`, so re-running skips finished steps unless `--force`.

**Scheduling**
- **Production:** Vercel Cron — `30 3 * * 1` (Mon 09:00 IST) → `/api/cron/weekly` → enqueues a run.
- **On-demand:** UI "Generate Weekly Pulse" button → `/api/run`.
- **Local:** `python -m orchestrator.run_weekly` or `cron` on a workstation.

---

## 6. Config & secrets (`.env.example`)

```
# --- LLM ---
GROQ_API_KEY=
GROQ_MODEL_REASONING=llama-3.1-70b-versatile
GROQ_MODEL_FAST=llama-3.1-8b-instant

# --- Source ---
PLAYSTORE_APP_ID=com.nextbillion.groww
WEEKS_LOOKBACK=12              # minimum 12, may go up to 26
LANG=en
COUNTRY=in

# --- Email ---
EMAIL_MODE=draft               # draft | send
ALERT_EMAIL=you@example.com
RESEND_API_KEY=                # preferred on Vercel
SMTP_HOST=smtp.gmail.com       # optional fallback
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=

# --- Vercel runtime (auto-injected on deploy, set locally for `vercel dev`) ---
BLOB_READ_WRITE_TOKEN=
KV_URL=
KV_REST_API_URL=
KV_REST_API_TOKEN=
KV_REST_API_READ_ONLY_TOKEN=

# --- Job queue ---
QSTASH_URL=https://qstash.upstash.io
QSTASH_TOKEN=
QSTASH_CURRENT_SIGNING_KEY=
QSTASH_NEXT_SIGNING_KEY=

# --- Cron auth ---
CRON_SECRET=                   # Vercel sets this; verified inside /api/cron/weekly

# --- Local dev toggle ---
RUN_LOCAL=0                    # 1 = use filesystem + in-memory KV instead of Vercel
```

---

## 7. PII handling — explicit guarantees

Because the brief calls this out:

| Layer | What it removes |
|---|---|
| Phase 2 regex | emails, phones, UPI IDs, PAN, Aadhaar-shaped, URLs, long digit strings |
| Phase 2 NER | `PERSON` names → `[USER]` |
| Phase 3 prompt | "Treat any remaining names as `[USER]`. Do not echo identifiers." |
| Phase 4 quote picker | extra regex pass before quoting; reject quote if any pattern matches |

A unit test in `tests/test_pii.py` runs a fixture of 50 known-bad strings and asserts zero leakage in the final pulse.

---

## 8. Testing strategy

- **Phase 1:** mock `google-play-scraper`; assert date-window filter.
- **Phase 2:** golden-file tests on PII fixtures.
- **Phase 3:** snapshot test of Groq JSON parser; mock LLM with canned responses to verify schema retries.
- **Phase 4:** template renders with synthetic theme data; assert ≤ 350 words and exactly 3+3+3 sections.
- **Phase 5:** `.eml` output validates against `email.parser.BytesParser`.

---

## 9. Deliverables for the submission

1. **Public Vercel URL** — e.g. `https://groww-pulse.vercel.app` showing the latest pulse and a working "Generate Weekly Pulse" button.
2. `pulse_2026-W19.md` — the one-pager (downloadable from the UI; also stored in Vercel Blob).
3. `pulse_2026-W19.eml` — the drafted email (downloadable from the UI).
4. `README.md` — how to run locally (CLI + `vercel dev`) and how to deploy.
5. `requirements.txt` (Python) + `phase6_ui/package.json` (Node).
6. `vercel.json` with cron + function config.

---

## 10. Build sequence (when you're ready to code)

A natural order that lets you demo something at every step:

1. **Phase 1 standalone** — print latest 100 reviews (12-week window).
2. **Phase 2** — show before/after PII diffs on 10 samples.
3. **Phase 3 Stage A only** — print discovered themes for the dataset.
4. **Phase 3 Stage B** — counts per theme.
5. **Phase 4** — render `pulse.md` to stdout.
6. **Phase 5 `draft` mode** → `.eml`.
7. **Phase 5 `send` mode** → real inbox (Resend).
8. Refactor — extract reusable `pipeline.run_all(...)` with `Storage` / `StateStore` protocols and `on_progress` callback.
9. **Phase 6a — UI shell.** Scaffold Next.js in `phase6_ui/`, wire Tailwind + shadcn, render a static sample `pulse.json`.
10. **Phase 6b — Read API.** Implement `api/pulse.py` and `api/status.py` against local FS storage; UI fetches the latest pulse.
11. **Phase 6c — Run API.** Implement `api/run.py` + `api/worker.py`. Test end-to-end with `vercel dev` (still local FS / in-memory KV).
12. **Phase 6d — Vercel storage.** Switch `Storage` and `StateStore` to Vercel Blob + Vercel KV; wire QStash for the queue.
13. **Phase 6e — Cron.** Add `api/cron/weekly.py` and the cron entry in `vercel.json`.
14. **Phase 6f — Polish.** History page, download buttons, "Send Email" button, error states, loading skeletons.
15. **Deploy.** `vercel --prod`; verify cron + manual run + email both work in production.

---

## 11. Cost & performance notes (Groq)

- Theme discovery: 1 call, ~3k tokens in / 500 out → negligible.
- Classification: ~N/20 calls on the fast model. For N = 2,000 (12-week window) → ~100 calls, ~600k tokens total. Within Groq free-tier limits.
- Action generation: 1 call, ~2k tokens.
- End-to-end runtime target: **< 3 minutes** in the worker — fits Vercel Pro `maxDuration: 300`.

**Vercel-specific notes**
- Pin functions to region `bom1` (Mumbai) — Play Store fetches and Resend latency both improve.
- `api/worker.py` does cold-start spaCy load (~700 MB peak) — set `memory: 1024` and avoid loading inside `api/run.py` (kept lightweight to stay snappy for the user).
- Vercel Blob egress is free up to a generous monthly allowance; the pulse artefacts are tiny (< 1 MB / run).
- Hobby plan limit is 60 s per function. If staying on Hobby, the queue + worker pattern is mandatory **and** classification must be parallelised aggressively (or the worker re-enqueues itself with a checkpoint after each phase).

---

## 12. Future extensions (out of scope for v1)

- Multi-language support (Hindi, Tamil) via Groq translation step.
- Sentiment trend chart (week-over-week) — Recharts in the UI, also attached to the email.
- Slack delivery (Vercel function calls Slack incoming webhook) in addition to email.
- iOS App Store source (`app-store-scraper`).
- Compare against competitor apps (Zerodha Kite, Upstox) — toggle in the UI.
- Auth on the UI via NextAuth (Google SSO) for leadership read-only access.
- Streaming progress via Server-Sent Events instead of polling.
