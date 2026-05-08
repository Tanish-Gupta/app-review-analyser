"""Phase 4 runner: build one-page weekly pulse from themed reviews."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings  # noqa: E402
from phase4_pulse.src.pulse_builder import build_pulse, save_pulse_artifacts  # noqa: E402

logger = logging.getLogger(__name__)


def _extract_run_id(path: Path) -> str:
    m = re.match(r"themed_reviews_(.+)\.parquet$", path.name)
    return m.group(1) if m else "manual"


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 4 — build weekly pulse")
    parser.add_argument("--input", required=True, help="Path to themed_reviews_<run_id>.parquet")
    parser.add_argument("--themes", required=True, help="Path to themes_<run_id>.json")
    parser.add_argument("--run-id", default=None, help="Optional run id override")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
    )

    in_path = Path(args.input)
    themes_path = Path(args.themes)
    if not in_path.exists():
        raise FileNotFoundError(f"Missing input parquet: {in_path}")
    if not themes_path.exists():
        raise FileNotFoundError(f"Missing themes json: {themes_path}")

    run_id = args.run_id or _extract_run_id(in_path)
    themed_df = pd.read_parquet(in_path)
    themes_payload = json.loads(themes_path.read_text(encoding="utf-8"))

    templates_dir = Path(__file__).resolve().parent / "src" / "templates"
    md_t = (templates_dir / "pulse.md.j2").read_text(encoding="utf-8")
    html_t = (templates_dir / "pulse.html.j2").read_text(encoding="utf-8")

    pulse = build_pulse(
        themed_df=themed_df,
        themes_payload=themes_payload,
        markdown_template=md_t,
        html_template=html_t,
        groq_api_key=settings.groq_api_key,
        groq_model=settings.groq_model_fast,
    )
    paths = save_pulse_artifacts(pulse=pulse, output_dir=settings.output_dir, run_id=run_id)

    print()
    print("Phase 4 complete")
    print("---------------")
    print(f"Input themed reviews: {in_path}")
    print(f"Input themes:         {themes_path}")
    print(f"Pulse markdown:       {paths['md']}")
    print(f"Pulse html:           {paths['html']}")
    print(f"Pulse json:           {paths['json']}")
    print(f"Top themes:           {', '.join([t['name'] for t in pulse['top_themes']])}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

