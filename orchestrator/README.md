# Orchestrator (planned)

Two pieces:

- `pipeline.py` — importable functions (`ingest`, `clean`, `discover_themes`,
  `classify`, `build_pulse`, `email`, `run_all`) backed by `Storage` and
  `StateStore` protocols so the same code runs locally (filesystem +
  in-memory dict) and on Vercel (Blob + KV).
- `run_weekly.py` — thin CLI wrapper around `run_all` for local / cron use.

> Not yet implemented — see `architecture.md` § 5.
