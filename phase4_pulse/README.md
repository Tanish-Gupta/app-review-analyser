# Phase 4 — Weekly Pulse Builder

Builds the one-page pulse from themed reviews.

What it does:

- picks top 3 themes by `0.5*volume_share + 0.5*negative_share`
- selects 3 representative quotes (one per top theme)
- generates 3 action ideas (Groq-backed with deterministic fallback)
- renders markdown + html + json artifacts

## Run

```bash
python -m phase4_pulse.run \
  --input data/interim/themed_reviews_<run_id>.parquet \
  --themes data/interim/themes_<run_id>.json
```

## Output

- `data/output/pulse_<run_id>.md`
- `data/output/pulse_<run_id>.html`
- `data/output/pulse_<run_id>.json`
