"""Pipeline stderr → short UI hints (keep in sync with phase6_ui/lib/runPipeline.ts)."""

from __future__ import annotations

import re

PIP_NAME_OVERRIDES = {"google_play_scraper": "google-play-scraper"}


def pipeline_failure_hint(stderr: str) -> str:
    s = stderr.lower()

    mod_match = re.search(r"No module named ['\"]([^'\"]+)['\"]", stderr)
    if mod_match:
        mod = mod_match.group(1)
        pip = PIP_NAME_OVERRIDES.get(mod, mod)
        return (
            f"Pipeline failed: missing Python package for module `{mod}`. "
            f"Install: `python3 -m pip install {pip}` or `pip install -r requirements.txt`."
        )

    groq_http = re.search(r"Groq HTTP (\d{3})", stderr, re.I)
    if groq_http:
        code = groq_http.group(1)
        if code == "429":
            return (
                "Pipeline failed: Groq rate limit or daily token quota (HTTP 429). "
                "Wait, lower PHASE3_MAX_ROWS, or upgrade — see detail."
            )
        if code in ("401", "403"):
            return (
                f"Pipeline failed: Groq rejected the key (HTTP {code}). "
                "Check GROQ_API_KEY in environment."
            )
        return f"Pipeline failed: Groq API returned HTTP {code}. See detail."

    if "rate_limit_exceeded" in s or "tokens per day" in s:
        return (
            "Pipeline failed: Groq rate limit or daily quota. Wait or reduce PHASE3_MAX_ROWS."
        )

    if (
        "invalid_api_key" in s
        or "invalid api key" in s
        or "incorrect api key" in s
    ):
        return "Pipeline failed: check GROQ_API_KEY is valid."

    if "groqerror" in s or "groq request failed" in s:
        return "Pipeline failed during Groq requests — see detail (often quota, not a missing key)."

    return (
        "Pipeline failed (ingest → pulse). Check dependencies, GROQ_API_KEY, network, detail."
    )
