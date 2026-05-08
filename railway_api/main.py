"""HTTP API for Play Store pipeline + email — deploy on Railway (Docker)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from config.settings import PROJECT_ROOT, settings

from railway_api.hints import pipeline_failure_hint
from railway_api.session_cache import get_cached_run_id_for_weeks

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Groww Pulse Pipeline API", version="1.0.0")

_origins = os.environ.get("CORS_ORIGINS", "*").strip()
if _origins == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def verify_bearer(authorization: Annotated[str | None, Header()] = None) -> None:
    secret = (os.environ.get("RAILWAY_API_SECRET") or "").strip()
    if not secret:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if token != secret:
        raise HTTPException(status_code=403, detail="Invalid API secret")


class PipelineRunBody(BaseModel):
    weeks: int = Field(default=12, ge=12, le=26)


class EmailBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    weeks: int = Field(default=12, ge=12, le=26)
    recipient: str = Field(min_length=3)
    recipient_name: str | None = Field(default=None, alias="recipientName")
    mode: Literal["draft", "send"] = "draft"
    force_refresh: bool = Field(default=False, alias="forceRefresh")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/pipeline/run")
def run_pipeline(
    body: PipelineRunBody,
    _: Annotated[None, Depends(verify_bearer)],
):
    settings.ensure_dirs()
    cmd = [
        sys.executable,
        "-m",
        "orchestrator.run_pipeline",
        "--weeks",
        str(body.weeks),
    ]
    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        env={**os.environ},
        capture_output=True,
        text=True,
    )
    err = (proc.stderr or "") + (proc.stdout or "")
    if proc.returncode != 0:
        return JSONResponse(
            status_code=500,
            content={
                "error": pipeline_failure_hint(err),
                "detail": err[-2000:],
            },
        )
    session_path = PROJECT_ROOT / "data" / "cache" / "session.json"
    try:
        run_id = json.loads(session_path.read_text(encoding="utf-8")).get("runId")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Could not read session.json", "detail": str(e)},
        )
    if not run_id:
        return JSONResponse(
            status_code=500,
            content={"error": "session.json missing runId", "detail": ""},
        )
    return {
        "runId": run_id,
        "weeks": body.weeks,
        "hint": "Pulse written to data/output/.",
    }


@app.post("/v1/email")
def send_email_route(
    body: EmailBody,
    _: Annotated[None, Depends(verify_bearer)],
):
    settings.ensure_dirs()
    recipient = body.recipient.strip()
    if not recipient:
        return JSONResponse(status_code=400, content={"error": "recipient is required"})

    run_id: str | None = None
    used_cache = False

    if not body.force_refresh:
        cached = get_cached_run_id_for_weeks(body.weeks)
        if cached:
            run_id = cached
            used_cache = True

    if not run_id:
        cmd = [
            sys.executable,
            "-m",
            "orchestrator.run_pipeline",
            "--weeks",
            str(body.weeks),
        ]
        proc = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            env={**os.environ},
            capture_output=True,
            text=True,
        )
        err = (proc.stderr or "") + (proc.stdout or "")
        if proc.returncode != 0:
            return JSONResponse(
                status_code=500,
                content={
                    "error": pipeline_failure_hint(err),
                    "detail": err[-2000:],
                },
            )
        session_path = PROJECT_ROOT / "data" / "cache" / "session.json"
        try:
            run_id = json.loads(session_path.read_text(encoding="utf-8")).get("runId")
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": "Could not read session after pipeline", "detail": str(e)},
            )
        if not run_id:
            return JSONResponse(
                status_code=500,
                content={"error": "No runId after pipeline", "detail": ""},
            )

    out = settings.output_dir
    json_p = out / f"pulse_{run_id}.json"
    md_p = out / f"pulse_{run_id}.md"
    html_p = out / f"pulse_{run_id}.html"
    if not all(p.is_file() for p in (json_p, md_p, html_p)):
        return JSONResponse(
            status_code=404,
            content={"error": f"Pulse artifacts missing for run {run_id}"},
        )

    args = [
        sys.executable,
        "-m",
        "phase5_email.run",
        "--pulse-json",
        str(json_p),
        "--pulse-md",
        str(md_p),
        "--pulse-html",
        str(html_p),
        "--mode",
        body.mode,
        "--recipient",
        recipient,
    ]
    if body.recipient_name and body.recipient_name.strip():
        args.extend(["--recipient-name", body.recipient_name.strip()])

    proc = subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        env={**os.environ},
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or "")[-1500:]
        return JSONResponse(
            status_code=500,
            content={
                "error": "phase5_email.run failed. Check SMTP / Resend env vars.",
                "detail": tail,
            },
        )

    cache_hint = (
        "Reused pulse from cache (same week range, completed within the last 24 hours)."
        if used_cache
        else "Built fresh from latest Play Store data."
    )
    msg = (
        f"Draft saved · {run_id}. {cache_hint}"
        if body.mode == "draft"
        else f"Sent · {run_id}. {cache_hint}"
    )
    return {"ok": True, "runId": run_id, "usedCache": used_cache, "message": msg}


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    import uvicorn

    uvicorn.run(
        "railway_api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
