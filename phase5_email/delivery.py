"""Programmatic Phase 5 entrypoint for CLI and future frontend / API.

Recipient is supplied per request (e.g. from the UI). The envelope **From**
address comes only from configuration (`EMAIL_FROM` or legacy `ALERT_EMAIL`) —
never pass an untrusted From address from the client.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from email.utils import parseaddr
from pathlib import Path
from typing import Literal

from config.settings import Settings, settings as default_settings
from phase5_email.src.email_html import apply_fancy_email_shell
from phase5_email.src.mailer import append_email_log, create_draft_eml, send_email
from phase5_email.src.personalize import personalize_email_bodies, sanitize_recipient_name

# Pragmatic RFC 5322–oriented check; avoids accepting obvious garbage.
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email_address(addr: str, *, field: str = "email") -> str:
    """Strip, validate, return normalized address. Raises ValueError if invalid."""
    cleaned = (addr or "").strip()
    if not cleaned:
        raise ValueError(f"{field} is required")
    _, spec = parseaddr(cleaned)
    candidate = spec if spec else cleaned
    if not _EMAIL_RE.match(candidate):
        raise ValueError(f"Invalid {field}: {addr!r}")
    return candidate


def resolve_sender(
    *,
    settings: Settings,
    sender_override: str | None = None,
) -> str:
    """Resolved From address: explicit override, then EMAIL_FROM, then ALERT_EMAIL."""
    if sender_override:
        return validate_email_address(sender_override, field="sender")
    for cand in (settings.email_from, settings.alert_email):
        if cand and str(cand).strip():
            return validate_email_address(str(cand).strip(), field="sender")
    raise ValueError(
        "Configure EMAIL_FROM (recommended) or ALERT_EMAIL for the From address, "
        "or pass sender_override for local testing only."
    )


def resolve_recipient(
    *,
    settings: Settings,
    recipient: str | None = None,
) -> str:
    """Resolved To address: explicit recipient (e.g. from frontend), else ALERT_EMAIL."""
    if recipient and str(recipient).strip():
        return validate_email_address(str(recipient).strip(), field="recipient")
    if settings.alert_email and str(settings.alert_email).strip():
        return validate_email_address(str(settings.alert_email).strip(), field="recipient")
    raise ValueError(
        "recipient is required (pass from the frontend/API) or set ALERT_EMAIL for CLI defaults."
    )


def send_transport_available(settings: Settings) -> bool:
    if settings.resend_api_key:
        return True
    return bool(settings.smtp_user and settings.smtp_pass)


@dataclass(frozen=True)
class PulseEmailResult:
    run_id: str
    pulse_json: Path
    draft_eml_path: Path | None
    send_channel: str | None
    recipient: str
    sender: str
    log_path: Path
    recipient_display_name: str | None = None


def _extract_run_id(path: Path) -> str:
    m = re.match(r"pulse_(.+)\.json$", path.name)
    return m.group(1) if m else "manual"


def deliver_pulse_email(
    *,
    pulse_json: Path,
    pulse_md: Path,
    pulse_html: Path,
    mode: Literal["draft", "send", "both"],
    settings: Settings | None = None,
    recipient: str | None = None,
    recipient_name: str | None = None,
    sender_override: str | None = None,
) -> PulseEmailResult:
    """Draft and/or send the pulse email.

    Parameters
    ----------
    recipient
        Destination inbox (required unless ``ALERT_EMAIL`` is set for CLI-style runs).
    recipient_name
        Display name for the greeting (e.g. ``Hi Jane,``). From the UI/session.
    sender_override
        Optional From address — intended for tests or trusted callers only; the
        frontend should leave this unset so ``EMAIL_FROM`` is used.
    """
    cfg = settings or default_settings
    effective_mode = mode

    if effective_mode in ("send", "both") and not send_transport_available(cfg):
        raise RuntimeError(
            "Send requires RESEND_API_KEY or SMTP_USER + SMTP_PASS in the environment."
        )

    sender = resolve_sender(settings=cfg, sender_override=sender_override)
    to_addr = resolve_recipient(settings=cfg, recipient=recipient)

    for p in (pulse_json, pulse_md, pulse_html):
        if not p.exists():
            raise FileNotFoundError(f"Missing pulse artifact: {p}")

    pulse = json.loads(pulse_json.read_text(encoding="utf-8"))
    md_body = pulse_md.read_text(encoding="utf-8")
    html_body = pulse_html.read_text(encoding="utf-8")
    display_name = sanitize_recipient_name(recipient_name)
    md_body, html_body = personalize_email_bodies(
        markdown_body=md_body,
        html_body=html_body,
        recipient_name=recipient_name,
    )
    run_id = _extract_run_id(pulse_json)
    subject = pulse.get("title", f"Groww Weekly Pulse — {run_id}")
    # Email multipart HTML part only — keeps Phase 4 pulse_*.html files unchanged on disk.
    html_body = apply_fancy_email_shell(html_body, document_title=subject)

    cfg.ensure_dirs()
    log_path = cfg.output_dir / "email_log.csv"
    out_eml: Path | None = None
    channel: str | None = None

    if effective_mode in ("draft", "both"):
        out_eml = cfg.output_dir / f"pulse_{run_id}.eml"
        create_draft_eml(
            subject=subject,
            sender=sender,
            recipient=to_addr,
            markdown_body=md_body,
            html_body=html_body,
            output_path=out_eml,
        )
        append_email_log(
            csv_path=log_path,
            run_id=run_id,
            mode="draft",
            status="ok",
            channel="eml",
            recipient=to_addr,
        )

    if effective_mode in ("send", "both"):
        channel = send_email(
            subject=subject,
            sender=sender,
            recipient=to_addr,
            markdown_body=md_body,
            html_body=html_body,
            resend_api_key=cfg.resend_api_key,
            smtp_host=cfg.smtp_host,
            smtp_port=cfg.smtp_port,
            smtp_user=cfg.smtp_user,
            smtp_pass=cfg.smtp_pass,
        )
        append_email_log(
            csv_path=log_path,
            run_id=run_id,
            mode="send",
            status="ok",
            channel=channel,
            recipient=to_addr,
        )

    return PulseEmailResult(
        run_id=run_id,
        pulse_json=pulse_json,
        draft_eml_path=out_eml,
        send_channel=channel,
        recipient=to_addr,
        sender=sender,
        log_path=log_path,
        recipient_display_name=display_name,
    )
