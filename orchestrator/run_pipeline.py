"""Run phases 1→4 with one shared run id (ingest through pulse build).

Usage (from repo root):
    python -m orchestrator.run_pipeline --weeks 12
    python -m orchestrator.run_pipeline --weeks 16 --run-id 2026-W19-custom

Writes ``data/cache/session.json`` with runId, weeks, completedAt on success.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def mint_run_id() -> str:
    now = datetime.now(timezone.utc)
    iso_year, iso_week, _ = now.isocalendar()
    return f"{iso_year}-W{iso_week:02d}-{now.strftime('%H%M%S')}"


def run_phase(cmd: list[str]) -> None:
    env = os.environ.copy()
    r = subprocess.run(cmd, cwd=ROOT, env=env)
    if r.returncode != 0:
        sys.exit(r.returncode)


def write_session(run_id: str, weeks: int) -> None:
    cache_dir = ROOT / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "runId": run_id,
        "weeks": weeks,
        "completedAt": datetime.now(timezone.utc).isoformat(),
    }
    (cache_dir / "session.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run phases 1–4 (ingest → pulse)")
    parser.add_argument("--weeks", type=int, default=12)
    parser.add_argument("--run-id", default=None, help="Optional fixed run id")
    args = parser.parse_args()

    run_id = args.run_id or mint_run_id()
    py = sys.executable

    run_phase([py, "-m", "phase1_ingest.run", "--weeks", str(args.weeks), "--run-id", run_id])

    raw_json = ROOT / "data" / "raw" / f"raw_reviews_{run_id}.json"
    run_phase([py, "-m", "phase2_clean.run", "--input", str(raw_json)])

    clean_parquet = ROOT / "data" / "interim" / f"clean_reviews_{run_id}.parquet"
    run_phase([py, "-m", "phase3_themes.run", "--input", str(clean_parquet)])

    themed_parquet = ROOT / "data" / "interim" / f"themed_reviews_{run_id}.parquet"
    themes_json = ROOT / "data" / "interim" / f"themes_{run_id}.json"
    run_phase(
        [
            py,
            "-m",
            "phase4_pulse.run",
            "--input",
            str(themed_parquet),
            "--themes",
            str(themes_json),
            "--run-id",
            run_id,
        ]
    )

    write_session(run_id, args.weeks)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
