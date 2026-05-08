# Phase 2 — Clean + PII Scrub

Takes the raw JSON from Phase 1 and produces analysis-ready, PII-reduced
reviews in parquet format.

## What is implemented

1. Exact dedupe by `review_id`
2. Near dedupe by normalized text hash (`sha1` over normalized first 300 chars)
3. Quality filter (`len(text) >= 15`)
4. Language filter (`langdetect`, keep only `en`)
5. PII scrub with regex replacement:
   - emails -> `[EMAIL]`
   - phone numbers -> `[PHONE]`
   - UPI handles -> `[UPI]`
   - PAN -> `[PAN]`
   - Aadhaar-like patterns -> `[AADHAAR]`
   - URLs -> `[URL]`
   - long digit strings -> `[ACCOUNT_ID]`
6. Optional spaCy PERSON masking (`[USER]`) if `en_core_web_sm` is installed

## Output

`data/interim/clean_reviews_<run_id>.parquet`

Columns:

- `review_id`, `rating`, `title`, `text`, `text_clean`, `date`,
  `app_version`, `helpful_count`, `lang`, `near_dup_hash`

## Run

```bash
python -m phase2_clean.run \
  --input data/raw/raw_reviews_<run_id>.json
```

Optional flags:

- `--output <path>`
- `--min-chars 20`
- `-v`
