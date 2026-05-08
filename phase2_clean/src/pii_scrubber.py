from __future__ import annotations

import re
from functools import lru_cache

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_RE = re.compile(r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b")
UPI_RE = re.compile(r"\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b")
PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
LONG_DIGITS_RE = re.compile(r"\b\d{8,}\b")
WHITESPACE_RE = re.compile(r"\s+")


@lru_cache(maxsize=1)
def _maybe_load_spacy():
    try:
        import spacy

        return spacy.load("en_core_web_sm", disable=["tagger", "parser", "lemmatizer"])
    except Exception:
        return None


def scrub_pii(text: str) -> str:
    clean = text or ""
    clean = EMAIL_RE.sub("[EMAIL]", clean)
    clean = PHONE_RE.sub("[PHONE]", clean)
    clean = UPI_RE.sub("[UPI]", clean)
    clean = PAN_RE.sub("[PAN]", clean)
    clean = AADHAAR_RE.sub("[AADHAAR]", clean)
    clean = URL_RE.sub("[URL]", clean)
    clean = LONG_DIGITS_RE.sub("[ACCOUNT_ID]", clean)
    clean = _mask_person_entities(clean)
    clean = WHITESPACE_RE.sub(" ", clean).strip()
    return clean


def _mask_person_entities(text: str) -> str:
    nlp = _maybe_load_spacy()
    if nlp is None or not text:
        return text

    doc = nlp(text)
    if not doc.ents:
        return text

    parts: list[str] = []
    cursor = 0
    for ent in doc.ents:
        if ent.label_ != "PERSON":
            continue
        parts.append(text[cursor : ent.start_char])
        parts.append("[USER]")
        cursor = ent.end_char
    parts.append(text[cursor:])
    return "".join(parts)


def likely_contains_pii(text: str) -> bool:
    return bool(
        EMAIL_RE.search(text)
        or PHONE_RE.search(text)
        or UPI_RE.search(text)
        or PAN_RE.search(text)
        or AADHAAR_RE.search(text)
        or URL_RE.search(text)
        or LONG_DIGITS_RE.search(text)
    )

