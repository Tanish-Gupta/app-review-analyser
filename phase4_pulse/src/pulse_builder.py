from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from jinja2 import Template

from phase4_pulse.src.action_generator import generate_action_ideas
from phase3_themes.src.groq_client import GroqClient


def build_pulse(
    *,
    themed_df: pd.DataFrame,
    themes_payload: dict[str, Any],
    markdown_template: str,
    html_template: str,
    groq_api_key: str | None,
    groq_model: str,
) -> dict[str, Any]:
    themes = themes_payload.get("themes", [])
    theme_map = {t["id"]: t for t in themes}

    grouped = (
        themed_df.groupby("theme_id")
        .agg(
            review_count=("review_id", "count"),
            avg_rating=("rating", "mean"),
            negative_count=("rating", lambda s: int((s <= 2).sum())),
        )
        .reset_index()
    )
    total = max(1, len(themed_df))
    grouped["volume_share"] = grouped["review_count"] / total
    grouped["negative_share"] = grouped["negative_count"] / grouped["review_count"].clip(lower=1)
    grouped["score"] = 0.5 * grouped["volume_share"] + 0.5 * grouped["negative_share"]
    grouped = grouped.sort_values("score", ascending=False).reset_index(drop=True)

    top3 = []
    for row in grouped.head(3).itertuples(index=False):
        meta = theme_map.get(row.theme_id, {"name": row.theme_id, "definition": row.theme_id})
        top3.append(
            {
                "id": row.theme_id,
                "name": meta["name"],
                "definition": meta.get("definition", meta["name"]),
                "review_count": int(row.review_count),
                "volume_share": float(row.volume_share),
                "negative_share": float(row.negative_share),
                "avg_rating": float(row.avg_rating),
            }
        )

    quotes = _pick_quotes(themed_df, [t["id"] for t in top3])
    client = GroqClient(api_key=groq_api_key) if groq_api_key else None
    actions = generate_action_ideas(
        client=client,
        model=groq_model,
        top_themes=top3,
        quotes=quotes,
    )

    review_dates = pd.to_datetime(themed_df["date"], utc=True, errors="coerce")
    start = review_dates.min().date().isoformat() if not review_dates.isna().all() else "n/a"
    end = review_dates.max().date().isoformat() if not review_dates.isna().all() else "n/a"
    avg_rating = float(pd.to_numeric(themed_df["rating"], errors="coerce").mean())
    now = datetime.utcnow()
    year, week, _ = now.isocalendar()

    pulse = {
        "title": f"Groww Weekly Pulse — Week {week}, {year}",
        "week": int(week),
        "year": int(year),
        "generated_at": now.isoformat() + "Z",
        "review_count": int(len(themed_df)),
        "avg_rating": round(avg_rating, 2),
        "window_start": start,
        "window_end": end,
        "top_themes": top3,
        "quotes": quotes,
        "actions": actions,
    }

    md = Template(markdown_template).render(p=pulse)
    html = Template(html_template).render(p=pulse)
    pulse["markdown"] = md
    pulse["html"] = html
    return pulse


def _pick_quotes(df: pd.DataFrame, top_theme_ids: list[str]) -> list[dict[str, Any]]:
    quotes: list[dict[str, Any]] = []
    for tid in top_theme_ids:
        chunk = df[df["theme_id"] == tid].copy()
        if chunk.empty:
            continue
        chunk["text_len"] = chunk["text_clean"].astype(str).str.len()
        chunk = chunk[(chunk["text_len"] >= 40) & (chunk["text_len"] <= 260)]
        if chunk.empty:
            chunk = df[df["theme_id"] == tid].copy()
            chunk["text_len"] = chunk["text_clean"].astype(str).str.len()
        chunk = chunk.sort_values(["helpful_count", "text_len"], ascending=[False, False])
        row = chunk.iloc[0]
        quotes.append(
            {
                "theme_id": tid,
                "text": str(row["text_clean"])[:260],
                "rating": int(row["rating"]),
                "date": str(pd.to_datetime(row["date"]).date()),
            }
        )
    return quotes[:3]


def save_pulse_artifacts(*, pulse: dict[str, Any], output_dir: Path, run_id: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"pulse_{run_id}.md"
    html_path = output_dir / f"pulse_{run_id}.html"
    json_path = output_dir / f"pulse_{run_id}.json"
    md_path.write_text(pulse["markdown"], encoding="utf-8")
    html_path.write_text(pulse["html"], encoding="utf-8")
    json_path.write_text(json.dumps({k: v for k, v in pulse.items() if k not in {"markdown", "html"}}, indent=2), encoding="utf-8")
    return {"md": md_path, "html": html_path, "json": json_path}

