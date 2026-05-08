from __future__ import annotations

import json
import logging
import time
from typing import Any

import pandas as pd

from .groq_client import GroqClient, GroqError, GroqHTTPError

logger = logging.getLogger(__name__)


def classify_reviews(
    *,
    client: GroqClient,
    model: str,
    clean_df: pd.DataFrame,
    themes: list[dict[str, Any]],
    prompt_template: str,
    batch_size: int = 20,
    min_batch_size: int = 3,
    max_chars_per_request: int = 2400,
    throttle_seconds: float = 1.2,
) -> pd.DataFrame:
    """Classify all reviews using Groq with adaptive chunking.

    Strategy:
    - Start from batch_size.
    - Shrink a batch if it exceeds char budget.
    - On HTTP 413 / token errors, halve batch size and retry.
    - On HTTP 429 / TPM limits, wait and retry same batch.
    """
    if clean_df.empty:
        return clean_df.copy()

    fallback_tid = themes[0]["id"]
    theme_ids = {t["id"] for t in themes}
    rows = [
        {
            "review_id": str(r.review_id),
            "rating": int(r.rating),
            "text_clean": str(r.text_clean)[:180],
        }
        for r in clean_df.itertuples(index=False)
    ]

    assignments: list[dict[str, Any]] = []
    i = 0
    total = len(rows)
    effective_batch = max(min_batch_size, batch_size)

    while i < total:
        remaining = total - i
        current_size = min(effective_batch, remaining)
        batch_rows = rows[i : i + current_size]
        batch_rows = _fit_char_budget(batch_rows, max_chars=max_chars_per_request, min_size=min_batch_size)
        current_size = len(batch_rows)
        batch_attempts = 0

        while True:
            batch_attempts += 1
            try:
                user_prompt = (
                    prompt_template.replace("{themes_json}", json.dumps(themes, ensure_ascii=True))
                    .replace("{reviews_json}", json.dumps(batch_rows, ensure_ascii=True))
                )
                payload = client.chat_json(
                    model=model,
                    system_prompt=(
                        "You are a review classifier. Return strict JSON only with an 'assignments' array."
                    ),
                    user_prompt=user_prompt,
                    temperature=0.0,
                )
                batch_assignments = _validate_assignments(
                    payload=payload,
                    batch_rows=batch_rows,
                    theme_ids=theme_ids,
                    fallback_tid=fallback_tid,
                )
                assignments.extend(batch_assignments)
                i += current_size
                logger.info(
                    "Classified %s/%s reviews (batch_size=%s, attempts=%s)",
                    i,
                    total,
                    current_size,
                    batch_attempts,
                )
                if effective_batch < batch_size:
                    effective_batch = min(batch_size, effective_batch + 1)
                time.sleep(throttle_seconds)
                break
            except GroqHTTPError as exc:
                body = exc.body.lower()
                if exc.status_code == 413 or ("requested" in body and "limit" in body):
                    if current_size > min_batch_size:
                        effective_batch = max(min_batch_size, current_size // 2)
                        batch_rows = batch_rows[:effective_batch]
                        current_size = len(batch_rows)
                        logger.warning(
                            "Batch too large (status=%s). Reducing batch to %s and retrying.",
                            exc.status_code,
                            effective_batch,
                        )
                        continue
                    logger.warning("Min batch still rate-limited; backing off 10s and retrying.")
                    time.sleep(10)
                    continue
                if exc.status_code == 429:
                    logger.warning("Rate limited (429). Backing off 12s and retrying.")
                    time.sleep(12)
                    continue
                raise
            except GroqError:
                # If parsing/format fails, shrink first. Fallback only after repeated failures at min size.
                if current_size > min_batch_size:
                    effective_batch = max(min_batch_size, current_size // 2)
                    batch_rows = batch_rows[:effective_batch]
                    current_size = len(batch_rows)
                    logger.warning(
                        "Batch parse failed. Shrinking to batch_size=%s and retrying.",
                        current_size,
                    )
                    continue
                if batch_attempts < 4:
                    logger.warning("Batch parse failed at min size; retrying after 4s.")
                    time.sleep(4)
                    continue
                logger.warning("Repeated parse failures at min size; applying fallback for %s rows.", current_size)
                for row in batch_rows:
                    assignments.append(
                        {
                            "review_id": row["review_id"],
                            "theme_id": fallback_tid,
                            "confidence": 0.35,
                        }
                    )
                i += current_size
                break

    assign_df = pd.DataFrame(assignments)
    out = clean_df.merge(assign_df, on="review_id", how="left")
    out["theme_id"] = out["theme_id"].fillna(fallback_tid)
    out["confidence"] = out["confidence"].fillna(0.4).astype(float)
    logger.info("Assigned %s reviews to %s themes (Groq LLM mode)", len(out), len(themes))
    return out


def _fit_char_budget(rows: list[dict[str, Any]], max_chars: int, min_size: int) -> list[dict[str, Any]]:
    out = rows
    while len(out) > min_size:
        chars = len(json.dumps(out, ensure_ascii=True))
        if chars <= max_chars:
            return out
        out = out[: max(min_size, len(out) - 1)]
    return out


def _validate_assignments(
    *,
    payload: dict[str, Any],
    batch_rows: list[dict[str, Any]],
    theme_ids: set[str],
    fallback_tid: str,
) -> list[dict[str, Any]]:
    batch_assignments = payload.get("assignments")
    if not isinstance(batch_assignments, list):
        raise GroqError(f"Missing assignments list: {payload}")

    valid_by_id: dict[str, dict[str, Any]] = {}
    for item in batch_assignments:
        rid = str(item.get("review_id", "")).strip()
        tid = str(item.get("theme_id", "")).strip()
        conf_raw = item.get("confidence", 0.5)
        try:
            conf = float(conf_raw)
        except Exception:
            conf = 0.5
        if not rid:
            continue
        if tid not in theme_ids:
            tid = fallback_tid
        valid_by_id[rid] = {"review_id": rid, "theme_id": tid, "confidence": max(0.0, min(1.0, conf))}

    out: list[dict[str, Any]] = []
    for row in batch_rows:
        rid = row["review_id"]
        out.append(valid_by_id.get(rid, {"review_id": rid, "theme_id": fallback_tid, "confidence": 0.4}))
    return out

