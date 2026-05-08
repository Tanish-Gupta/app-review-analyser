from __future__ import annotations

import hashlib
import re


_WS_RE = re.compile(r"\s+")


def _normalize_for_hash(text: str) -> str:
    text = (text or "").strip().lower()
    text = _WS_RE.sub(" ", text)
    return text


def near_duplicate_hash(text: str) -> str:
    normalized = _normalize_for_hash(text)
    # Keep the first chunk only to collapse tiny punctuation/ending edits.
    key = normalized[:300]
    return hashlib.sha1(key.encode("utf-8")).hexdigest()

