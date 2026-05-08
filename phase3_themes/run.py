"""Phase 3 runner: discover themes and classify cleaned reviews."""

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
from phase3_themes.src.groq_client import GroqClient  # noqa: E402
from phase3_themes.src.theme_classifier import classify_reviews  # noqa: E402
from phase3_themes.src.theme_discovery import discover_themes  # noqa: E402

logger = logging.getLogger(__name__)


def _extract_run_id(path: Path) -> str:
    m = re.match(r"clean_reviews_(.+)\.parquet$", path.name)
    return m.group(1) if m else "manual"


def _load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _resolve_model(available: list[str], preferred: str, fallbacks: list[str]) -> str:
    if preferred in available:
        return preferred
    for cand in fallbacks:
        if cand in available:
            logger.warning("Model %s unavailable. Falling back to %s", preferred, cand)
            return cand
    # Last resort: first available model
    if not available:
        raise RuntimeError("Groq returned no models")
    logger.warning("Model %s unavailable. Falling back to first available model %s", preferred, available[0])
    return available[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 — Groq themes + classification")
    parser.add_argument("--input", required=True, help="Path to clean_reviews_<run_id>.parquet")
    parser.add_argument("--themes-output", default=None, help="Path to write themes JSON")
    parser.add_argument("--classified-output", default=None, help="Path to write themed parquet")
    parser.add_argument("--sample-size", type=int, default=settings.phase3_sample_size)
    parser.add_argument("--batch-size", type=int, default=settings.phase3_batch_size)
    parser.add_argument(
        "--max-rows",
        type=int,
        default=settings.phase3_max_rows,
        help="Max reviews to classify (use 0 to disable cap)",
    )
    parser.add_argument("--discover-model", default=settings.groq_model_reasoning)
    parser.add_argument("--classify-model", default=settings.groq_model_fast)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
    )

    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to .env")

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input parquet not found: {input_path}")

    run_id = _extract_run_id(input_path)
    themes_output = Path(args.themes_output) if args.themes_output else settings.interim_dir / f"themes_{run_id}.json"
    classified_output = (
        Path(args.classified_output)
        if args.classified_output
        else settings.interim_dir / f"themed_reviews_{run_id}.parquet"
    )
    themes_output.parent.mkdir(parents=True, exist_ok=True)
    classified_output.parent.mkdir(parents=True, exist_ok=True)

    clean_df = pd.read_parquet(input_path)
    if args.max_rows and args.max_rows > 0:
        clean_df = clean_df.head(args.max_rows).copy()
        logger.info("Applying max-rows cap: %s", args.max_rows)
    logger.info("Loaded %s cleaned reviews from %s", len(clean_df), input_path)
    if clean_df.empty:
        raise RuntimeError("Input dataframe is empty. Cannot discover themes.")

    prompts_dir = Path(__file__).resolve().parent / "src" / "prompts"
    discover_prompt = _load_prompt(prompts_dir / "discover_themes.txt")
    classify_prompt = _load_prompt(prompts_dir / "classify_review.txt")

    client = GroqClient(api_key=settings.groq_api_key)
    available_models = client.list_models()
    discover_model = _resolve_model(
        available_models,
        args.discover_model,
        [
            "llama-3.1-8b-instant",
            "qwen/qwen3-32b",
            "openai/gpt-oss-120b",
            "groq/compound-mini",
        ],
    )
    classify_model = _resolve_model(
        available_models,
        args.classify_model,
        [
            "llama-3.1-8b-instant",
            "qwen/qwen3-32b",
            "groq/compound-mini",
        ],
    )

    logger.info("Discovering themes with model=%s", discover_model)
    themes = discover_themes(
        client=client,
        model=discover_model,
        clean_df=clean_df,
        prompt_template=discover_prompt,
        sample_size=args.sample_size,
    )
    logger.info("Discovered %s themes", len(themes))

    logger.info("Classifying reviews with model=%s and adaptive batching", classify_model)
    themed_df = classify_reviews(
        client=client,
        model=classify_model,
        clean_df=clean_df,
        themes=themes,
        prompt_template=classify_prompt,
        batch_size=args.batch_size,
    )

    themes_payload = {
        "run_id": run_id,
        "theme_count": len(themes),
        "themes": themes,
        "classification_mode": "groq_llm_batched",
        "classification_model": classify_model,
    }
    themes_output.write_text(json.dumps(themes_payload, indent=2), encoding="utf-8")
    logger.info("Saved themes + keywords to %s", themes_output)
    themed_df.to_parquet(classified_output, index=False)
    logger.info("Saved themed reviews to %s", classified_output)

    counts = themed_df["theme_id"].value_counts().to_dict()

    print()
    print("Phase 3 complete")
    print("---------------")
    print(f"Input file:        {input_path}")
    print(f"Themes file:       {themes_output}")
    print(f"Classified file:   {classified_output}")
    print(f"Rows classified:   {len(themed_df)}")
    print(f"Themes discovered: {len(themes)}")
    print("Theme distribution:")
    for t in themes:
        print(f"  {t['id']} - {t['name']}: {counts.get(t['id'], 0)}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

