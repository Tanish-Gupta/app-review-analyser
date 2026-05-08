"""Phase 1 — Ingest Play Store reviews (standalone runner).

Usage:
    python -m phase1_ingest.run                 # uses settings from .env / defaults
    python -m phase1_ingest.run --weeks 16
    python -m phase1_ingest.run --run-id 2026-W19-test
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the project root is importable when running as `python -m phase1_ingest.run`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings  # noqa: E402
from phase1_ingest.src.playstore_scraper import PlayStoreScraper  # noqa: E402


def _default_run_id() -> str:
    now = datetime.now(timezone.utc)
    iso_year, iso_week, _ = now.isocalendar()
    return f"{iso_year}-W{iso_week:02d}-{now.strftime('%H%M%S')}"


def _print_summary(run_id: str, app_id: str, weeks: int, reviews_list, out_path: Path) -> None:
    print()
    print(f"  Run ID:     {run_id}")
    print(f"  App:        {app_id}")
    print(f"  Window:     last {weeks} weeks")
    print(f"  Reviews:    {len(reviews_list)}")
    print(f"  Saved to:   {out_path}")
    print()

    if not reviews_list:
        return

    print("  Rating distribution")
    print("  -------------------")
    total = len(reviews_list)
    for star in range(5, 0, -1):
        n = sum(1 for r in reviews_list if r.rating == star)
        bar = "█" * int(40 * n / total) if total else ""
        pct = (n / total) * 100
        print(f"  {star}*  {n:>5}  ({pct:5.1f}%)  {bar}")

    avg = sum(r.rating for r in reviews_list) / total
    print()
    print(f"  Avg rating: {avg:.2f}")

    earliest = min(r.date for r in reviews_list)
    latest = max(r.date for r in reviews_list)
    print(f"  Span:       {earliest.date()} -> {latest.date()}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 1 — ingest Play Store reviews for the configured app"
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=settings.weeks_lookback,
        help="Weeks lookback (minimum 12, default from settings)",
    )
    parser.add_argument(
        "--app-id",
        default=settings.playstore_app_id,
        help="Play Store package id (default: %(default)s)",
    )
    parser.add_argument(
        "--lang", default=settings.lang, help="Review language (default: %(default)s)"
    )
    parser.add_argument(
        "--country",
        default=settings.country,
        help="Play Store country code (default: %(default)s)",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run identifier (defaults to YYYY-Www-HHMMSS)",
    )
    parser.add_argument(
        "--out-dir",
        default=str(settings.raw_dir),
        help="Where to write the raw reviews JSON (default: data/raw/)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable DEBUG logging"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
    )

    settings.ensure_dirs()
    run_id = args.run_id or _default_run_id()
    out_path = Path(args.out_dir) / f"raw_reviews_{run_id}.json"

    scraper = PlayStoreScraper(
        app_id=args.app_id,
        lang=args.lang,
        country=args.country,
        weeks_lookback=args.weeks,
    )
    reviews_list = scraper.fetch()
    scraper.save(reviews_list, out_path)
    _print_summary(run_id, args.app_id, scraper.weeks_lookback, reviews_list, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
