"""Phase 2 runner: clean + PII scrub + language filter.

Usage:
  python -m phase2_clean.run --input data/raw/raw_reviews_<run_id>.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings  # noqa: E402
from phase2_clean.src.processor import clean_reviews  # noqa: E402


logger = logging.getLogger(__name__)


def _extract_run_id(path: Path) -> str:
    m = re.match(r"raw_reviews_(.+)\.json$", path.name)
    return m.group(1) if m else "manual"


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2 — clean and scrub raw reviews")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to raw_reviews_<run_id>.json from phase1",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output parquet path (defaults to data/interim/clean_reviews_<run_id>.parquet)",
    )
    parser.add_argument("--min-chars", type=int, default=15, help="Minimum review length to keep")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
    )

    settings.ensure_dirs()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    payload = json.loads(input_path.read_text())
    raw_reviews = payload.get("reviews", [])
    run_id = _extract_run_id(input_path)
    output_path = Path(args.output) if args.output else settings.interim_dir / f"clean_reviews_{run_id}.parquet"

    logger.info("Loaded %s rows from %s", len(raw_reviews), input_path)
    cleaned_df, stats = clean_reviews(raw_reviews, min_chars=args.min_chars)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_parquet(output_path, index=False)

    print()
    print("Phase 2 complete")
    print("---------------")
    print(f"Input file:            {input_path}")
    print(f"Output file:           {output_path}")
    print(f"Input rows:            {stats.input_rows}")
    print(f"After exact dedupe:    {stats.after_exact_dedupe}")
    print(f"After near dedupe:     {stats.after_near_dedupe}")
    print(f"After quality filter:  {stats.after_quality_filter}")
    print(f"After lang filter:     {stats.after_lang_filter}")
    print(f"Final output rows:     {stats.output_rows}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

