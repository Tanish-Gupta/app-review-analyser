# Phase 1 — Ingest

Pulls **at least the last 12 weeks** of Play Store reviews for the configured app
(default: `com.nextbillion.groww`) and writes them to
`data/raw/raw_reviews_<run_id>.json`.

## What it does

- Paginates `google-play-scraper`'s `reviews(...)` endpoint sorted by NEWEST.
- Stops as soon as a page contains a review older than the cutoff date.
- Retries each page up to 3× with exponential backoff on transient errors.
- Drops Play Store-side PII (`userName`, `userImage`) at the model boundary —
  Phase 2 still scrubs the body text.
- Deduplicates by `reviewId`.
- Persists run metadata + rows in a single JSON file.

## Files

| File | Purpose |
|---|---|
| `src/models.py` | `Review` pydantic model + `Review.from_play_store(...)` adapter |
| `src/playstore_scraper.py` | `PlayStoreScraper` — paginated fetch with retry/backoff |
| `run.py` | CLI runner: `python -m phase1_ingest.run` |

## Output schema

```jsonc
{
  "app_id": "com.nextbillion.groww",
  "lang": "en",
  "country": "in",
  "weeks_lookback": 12,
  "fetched_at": "2026-05-08T11:31:02+00:00",
  "count": 1284,
  "reviews": [
    {
      "review_id": "...",
      "rating": 4,
      "title": "Loving the new charts",
      "text": "Loving the new charts...",
      "date": "2026-05-07T18:22:11+00:00",
      "app_version": "27.4.1",
      "helpful_count": 12
    }
  ]
}
```

## Run it

```bash
# default — 12 weeks of Groww reviews from the IN store, English
python -m phase1_ingest.run

# custom window
python -m phase1_ingest.run --weeks 16

# different app / locale
python -m phase1_ingest.run --app-id com.fivepaisa.trade --country in

# verbose
python -m phase1_ingest.run -v
```

The CLI prints a per-rating histogram, the average rating, and the date span
of the kept reviews.

## What this phase does **not** do

- No PII scrubbing of body text — that's Phase 2.
- No language filtering — Phase 2.
- No deduplication of near-duplicates (only exact `reviewId` matches) — Phase 2.

## Failure modes

- **Network blips** → 3 retries with 2s / 4s / 8s backoff.
- **App id not found** → `google-play-scraper` raises `NotFoundError` → propagated.
- **Empty result** → the runner exits cleanly with `count: 0`; later phases
  should detect this and short-circuit the pulse generation.
