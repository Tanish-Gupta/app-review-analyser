"""Play Store review scraper.

Uses paginated fetches via `google-play-scraper`'s `reviews(...)` endpoint
sorted by NEWEST, and stops as soon as we cross the configured cutoff date.
This is much cheaper than `reviews_all(...)` for popular apps like Groww.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google_play_scraper import Sort, reviews

from .models import Review

logger = logging.getLogger(__name__)

PAGE_SIZE = 200
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2.0


class PlayStoreScraper:
    def __init__(
        self,
        app_id: str,
        lang: str = "en",
        country: str = "in",
        weeks_lookback: int = 12,
    ) -> None:
        if weeks_lookback < 12:
            logger.warning(
                "weeks_lookback=%s below minimum; bumping to 12", weeks_lookback
            )
            weeks_lookback = 12
        self.app_id = app_id
        self.lang = lang
        self.country = country
        self.weeks_lookback = weeks_lookback

    def fetch(self) -> list[Review]:
        """Pull reviews newer than `now - weeks_lookback`, deduplicated."""
        cutoff = datetime.now(timezone.utc) - timedelta(weeks=self.weeks_lookback)
        logger.info(
            "Fetching reviews for app_id=%s lang=%s country=%s window=%s weeks (cutoff=%s)",
            self.app_id,
            self.lang,
            self.country,
            self.weeks_lookback,
            cutoff.isoformat(),
        )

        out: list[Review] = []
        seen: set[str] = set()
        token = None
        page = 0

        while True:
            page += 1
            batch, token = self._fetch_page(token)
            if not batch:
                logger.info("No more results on page %s — stopping.", page)
                break

            crossed_cutoff = False
            kept = 0
            for raw in batch:
                at = raw.get("at")
                if isinstance(at, datetime):
                    at_utc = at if at.tzinfo else at.replace(tzinfo=timezone.utc)
                else:
                    continue

                if at_utc < cutoff:
                    crossed_cutoff = True
                    break

                rid = str(raw.get("reviewId") or "")
                if not rid or rid in seen:
                    continue

                try:
                    review = Review.from_play_store(raw)
                except Exception as e:
                    logger.debug("Skipping malformed review: %s", e)
                    continue

                seen.add(rid)
                out.append(review)
                kept += 1

            logger.info(
                "Page %s: fetched=%s, kept=%s, total_kept=%s",
                page,
                len(batch),
                kept,
                len(out),
            )

            if crossed_cutoff:
                logger.info("Crossed cutoff date — stopping pagination.")
                break
            if token is None:
                logger.info("No continuation token — stopping pagination.")
                break

        logger.info("Done. Collected %s reviews.", len(out))
        return out

    def save(self, reviews_list: list[Review], path: Path) -> Path:
        """Persist as a single JSON file with run metadata + the rows."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "app_id": self.app_id,
            "lang": self.lang,
            "country": self.country,
            "weeks_lookback": self.weeks_lookback,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": len(reviews_list),
            "reviews": [r.model_dump(mode="json") for r in reviews_list],
        }
        path.write_text(json.dumps(payload, indent=2, default=str))
        logger.info("Saved %s reviews → %s", len(reviews_list), path)
        return path

    def _fetch_page(self, token):
        """Fetch one page of reviews with retry + exponential backoff."""
        last_err: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return reviews(
                    self.app_id,
                    lang=self.lang,
                    country=self.country,
                    sort=Sort.NEWEST,
                    count=PAGE_SIZE,
                    continuation_token=token,
                )
            except Exception as e:
                last_err = e
                wait = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "Fetch failed (attempt %s/%s): %s — retrying in %.1fs",
                    attempt,
                    MAX_RETRIES,
                    e,
                    wait,
                )
                time.sleep(wait)
        raise RuntimeError(
            f"Failed to fetch a page after {MAX_RETRIES} attempts"
        ) from last_err
