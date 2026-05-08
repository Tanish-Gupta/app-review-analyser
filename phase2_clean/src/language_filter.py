from __future__ import annotations

from langdetect import DetectorFactory, LangDetectException, detect

# Keep language detection deterministic between runs.
DetectorFactory.seed = 0


def detect_language(text: str) -> str:
    text = (text or "").strip()
    if len(text) < 20:
        return "unknown"
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

