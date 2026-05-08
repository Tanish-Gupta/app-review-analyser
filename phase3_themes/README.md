# Phase 3 — Theme Discovery & Grouping

Two-stage Groq pipeline:

- **Stage A — discovery**
  - takes a stratified sample of clean reviews (default: 150)
  - asks Groq for 3–5 non-overlapping themes
  - saves `themes_<run_id>.json`
- **Stage B — classification**
  - classifies every cleaned review into exactly one theme
  - batched Groq calls with adaptive chunking (default target: 20 reviews/request)
  - auto-shrinks on 413/token-limit errors and retries on 429
  - saves `themed_reviews_<run_id>.parquet`

## Implemented files

| File | Purpose |
|---|---|
| `src/groq_client.py` | OpenAI-compatible Groq HTTP client with retries |
| `src/theme_discovery.py` | Stratified sampling + theme generation |
| `src/theme_classifier.py` | Batch assignment of reviews to theme IDs |
| `src/prompts/discover_themes.txt` | Prompt template for theme discovery |
| `src/prompts/classify_review.txt` | Prompt template for classification |
| `run.py` | CLI entrypoint |

## Run

```bash
python -m phase3_themes.run \
  --input data/interim/clean_reviews_<run_id>.parquet
```

Optional flags:

- `--sample-size 150`
- `--batch-size 20`
- `--discover-model llama-3.1-70b-versatile`
- `--classify-model llama-3.1-8b-instant`

## Outputs

- `data/interim/themes_<run_id>.json`
- `data/interim/themed_reviews_<run_id>.parquet`
