"""Canonical Review model used by every later phase."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Review(BaseModel):
    """A single Play Store review, normalised."""

    review_id: str
    rating: int = Field(ge=1, le=5)
    title: str = ""
    text: str
    date: datetime
    app_version: str | None = None
    helpful_count: int = 0

    @field_validator("date")
    @classmethod
    def _ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    @classmethod
    def from_play_store(cls, raw: dict[str, Any]) -> "Review":
        """Build a Review from a `google-play-scraper` raw dict.

        The library returns roughly:
            {
              "reviewId": str,
              "userName": str,        # PII - intentionally dropped
              "userImage": str,       # PII - dropped
              "content": str,
              "score": int,           # 1-5
              "thumbsUpCount": int,
              "reviewCreatedVersion": str | None,
              "at": datetime,
              "replyContent": str | None,
              "repliedAt": datetime | None,
            }
        """
        text = (raw.get("content") or "").strip()
        title = _derive_title(text)

        return cls(
            review_id=str(raw["reviewId"]),
            rating=int(raw["score"]),
            title=title,
            text=text,
            date=raw["at"],
            app_version=raw.get("reviewCreatedVersion"),
            helpful_count=int(raw.get("thumbsUpCount") or 0),
        )


def _derive_title(text: str, max_len: int = 80) -> str:
    """Play Store reviews don't have titles. Use the first sentence as a stand-in."""
    if not text:
        return ""
    first = text.split(".", 1)[0].split("\n", 1)[0].strip()
    return first[:max_len]
