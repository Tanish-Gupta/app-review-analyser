"""Match phase6_ui/lib/pulseCache.ts: reuse session.json within TTL for same weeks."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config.settings import PROJECT_ROOT, settings

CACHE_TTL_MS = 24 * 60 * 60 * 1000


def _session_path() -> Path:
    return PROJECT_ROOT / "data" / "cache" / "session.json"


def _artifacts_exist(run_id: str) -> bool:
    out = settings.output_dir
    names = (
        f"pulse_{run_id}.json",
        f"pulse_{run_id}.md",
        f"pulse_{run_id}.html",
    )
    return all((out / n).is_file() for n in names)


def get_cached_run_id_for_weeks(weeks: int) -> str | None:
    p = _session_path()
    if not p.is_file():
        return None
    try:
        raw = p.read_text(encoding="utf-8")
        j = json.loads(raw)
        wid = j.get("weeks")
        run_id = j.get("runId")
        completed = j.get("completedAt")
        if wid != weeks or not run_id or not completed:
            return None
        ts = datetime.fromisoformat(str(completed).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age_ms = (datetime.now(timezone.utc) - ts).total_seconds() * 1000
        if age_ms < 0 or age_ms > CACHE_TTL_MS:
            return None
        if not _artifacts_exist(str(run_id)):
            return None
        return str(run_id)
    except Exception:
        return None
