from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .deduplicate import near_duplicate_hash
from .language_filter import detect_language
from .pii_scrubber import scrub_pii


@dataclass
class CleanStats:
    input_rows: int
    after_exact_dedupe: int
    after_near_dedupe: int
    after_quality_filter: int
    after_lang_filter: int
    output_rows: int


def clean_reviews(raw_reviews: list[dict[str, Any]], min_chars: int = 15) -> tuple[pd.DataFrame, CleanStats]:
    if not raw_reviews:
        empty = pd.DataFrame(
            columns=[
                "review_id",
                "rating",
                "title",
                "text",
                "text_clean",
                "date",
                "app_version",
                "helpful_count",
                "lang",
                "near_dup_hash",
            ]
        )
        stats = CleanStats(0, 0, 0, 0, 0, 0)
        return empty, stats

    df = pd.DataFrame(raw_reviews)
    input_rows = len(df)

    # 1) Exact dedupe by review_id.
    df = df.drop_duplicates(subset=["review_id"], keep="first").copy()
    after_exact = len(df)

    # 2) Near dedupe by normalized text hash.
    df["near_dup_hash"] = df["text"].astype(str).map(near_duplicate_hash)
    df = df.drop_duplicates(subset=["near_dup_hash"], keep="first").copy()
    after_near = len(df)

    # 3) Quality filter.
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() >= min_chars].copy()
    after_quality = len(df)

    # 4) Language filter (keep English only).
    df["lang"] = df["text"].map(detect_language)
    df = df[df["lang"] == "en"].copy()
    after_lang = len(df)

    # 5) PII scrub + whitespace normalization.
    df["text_clean"] = df["text"].map(scrub_pii)
    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df["helpful_count"] = pd.to_numeric(df["helpful_count"], errors="coerce").fillna(0).astype(int)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0).astype(int)

    df = df[
        [
            "review_id",
            "rating",
            "title",
            "text",
            "text_clean",
            "date",
            "app_version",
            "helpful_count",
            "lang",
            "near_dup_hash",
        ]
    ].reset_index(drop=True)

    stats = CleanStats(
        input_rows=input_rows,
        after_exact_dedupe=after_exact,
        after_near_dedupe=after_near,
        after_quality_filter=after_quality,
        after_lang_filter=after_lang,
        output_rows=len(df),
    )
    return df, stats

