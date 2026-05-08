from __future__ import annotations

import json
import random
from typing import Any

import pandas as pd

from .groq_client import GroqClient, GroqError


def _stratified_sample(df: pd.DataFrame, sample_size: int) -> pd.DataFrame:
    if len(df) <= sample_size:
        return df.copy()

    rng = random.Random(42)
    groups = []
    per_rating = max(1, sample_size // 5)
    for rating in [1, 2, 3, 4, 5]:
        chunk = df[df["rating"] == rating]
        if len(chunk) <= per_rating:
            groups.append(chunk)
        else:
            idx = list(chunk.index)
            picked = rng.sample(idx, per_rating)
            groups.append(chunk.loc[picked])
    sampled = pd.concat(groups, axis=0)
    if len(sampled) < sample_size:
        remaining = df.drop(sampled.index)
        take = min(sample_size - len(sampled), len(remaining))
        if take > 0:
            sampled = pd.concat([sampled, remaining.sample(n=take, random_state=42)], axis=0)
    return sampled.reset_index(drop=True)


def discover_themes(
    *,
    client: GroqClient,
    model: str,
    clean_df: pd.DataFrame,
    prompt_template: str,
    sample_size: int = 150,
    min_themes: int = 3,
    max_themes: int = 5,
) -> list[dict[str, Any]]:
    sampled = _stratified_sample(clean_df, sample_size=sample_size)
    rows = []
    for row in sampled.itertuples(index=False):
        rows.append(
            {
                "review_id": row.review_id,
                "rating": int(row.rating),
                "text_clean": str(row.text_clean)[:120],
            }
        )

    user_prompt = (
        prompt_template.replace("{min_themes}", str(min_themes))
        .replace("{max_themes}", str(max_themes))
        .replace("{reviews_json}", json.dumps(rows, ensure_ascii=True))
    )
    system_prompt = (
        "You are a senior product analyst. Return strict JSON only. "
        "No markdown. No prose outside JSON."
    )
    payload = client.chat_json(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
    )
    themes = payload.get("themes")
    if not isinstance(themes, list):
        raise GroqError(f"Expected 'themes' list in response. Got: {payload}")
    cleaned: list[dict[str, Any]] = []
    for idx, t in enumerate(themes[:max_themes], start=1):
        name = str(t.get("name", "")).strip()
        definition = str(t.get("definition", "")).strip()
        if not name:
            continue
        cleaned.append(
            {
                "id": f"T{idx}",
                "name": name,
                "definition": definition or name,
            }
        )
    if len(cleaned) < min_themes:
        raise GroqError(f"Model returned fewer than {min_themes} valid themes: {cleaned}")
    return cleaned[:max_themes]


def generate_theme_keywords(
    *,
    client: GroqClient,
    model: str,
    themes: list[dict[str, Any]],
) -> dict[str, list[str]]:
    user_prompt = (
        "Given these themes, produce compact keyword/phrase lexicons for matching reviews.\n"
        "Return strict JSON object only:\n"
        "{\n"
        '  "keywords": {\n'
        '    "T1": ["kw1", "kw2"],\n'
        '    "T2": ["kw1", "kw2"]\n'
        "  }\n"
        "}\n\n"
        f"Themes: {json.dumps(themes, ensure_ascii=True)}\n"
        "Rules: 12-20 keywords per theme, include spelling variants, keep lowercase."
    )
    payload = client.chat_json(
        model=model,
        system_prompt="You create strict JSON only.",
        user_prompt=user_prompt,
        temperature=0.0,
    )
    raw = payload.get("keywords", {})
    if not isinstance(raw, dict):
        raise GroqError(f"Invalid keywords payload: {payload}")
    out: dict[str, list[str]] = {}
    for t in themes:
        tid = t["id"]
        vals = raw.get(tid, [])
        if isinstance(vals, list):
            cleaned = [str(v).strip().lower() for v in vals if str(v).strip()]
        else:
            cleaned = []
        # Add theme name tokens as fallback.
        cleaned.extend(str(t["name"]).lower().split())
        out[tid] = sorted(set(cleaned))
    return out

