from __future__ import annotations

import csv
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import requests


def create_draft_eml(
    *,
    subject: str,
    sender: str,
    recipient: str,
    markdown_body: str,
    html_body: str,
    output_path: Path,
) -> Path:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg["X-Generated-By"] = "groww-pulse v0.1"
    msg.set_content(markdown_body)
    msg.add_alternative(html_body, subtype="html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(msg.as_bytes())
    return output_path


def send_email(
    *,
    subject: str,
    sender: str,
    recipient: str,
    markdown_body: str,
    html_body: str,
    resend_api_key: str | None,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str | None,
    smtp_pass: str | None,
) -> str:
    if resend_api_key:
        _send_with_resend(
            api_key=resend_api_key,
            subject=subject,
            sender=sender,
            recipient=recipient,
            html_body=html_body,
            text_body=markdown_body,
        )
        return "resend"

    if not smtp_user or not smtp_pass:
        raise RuntimeError("SMTP credentials missing and RESEND_API_KEY not set")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(markdown_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
    return "smtp"


def append_email_log(*, csv_path: Path, run_id: str, mode: str, status: str, channel: str, recipient: str) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["timestamp_utc", "run_id", "mode", "status", "channel", "recipient"])
        w.writerow(
            [
                datetime.now(timezone.utc).isoformat(),
                run_id,
                mode,
                status,
                channel,
                recipient,
            ]
        )


def _send_with_resend(*, api_key: str, subject: str, sender: str, recipient: str, html_body: str, text_body: str) -> None:
    url = "https://api.resend.com/emails"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "from": sender,
        "to": [recipient],
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"Resend send failed HTTP {resp.status_code}: {resp.text[:300]}")

