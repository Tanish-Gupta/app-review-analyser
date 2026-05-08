"""Prefix pulse bodies with a Hi <name>, greeting for plain-text and HTML."""

from __future__ import annotations

import html
import re


def sanitize_recipient_name(name: str | None) -> str | None:
    """Normalize display name: strip, collapse whitespace, cap length. Empty → None."""
    if name is None:
        return None
    s = " ".join(str(name).strip().split())
    if not s:
        return None
    return s[:200]


def personalize_email_bodies(
    *,
    markdown_body: str,
    html_body: str,
    recipient_name: str | None,
) -> tuple[str, str]:
    """Return bodies with a leading greeting when ``recipient_name`` is present."""
    display = sanitize_recipient_name(recipient_name)
    if not display:
        return markdown_body, html_body

    md_out = f"Hi {display},\n\n{markdown_body}"

    escaped = html.escape(display)
    greeting_html = (
        f'<p class="greeting" style="margin-bottom:16px;font-size:16px;">Hi {escaped},</p>'
    )

    def inject_after_body_open(m: re.Match[str]) -> str:
        return m.group(1) + "\n  " + greeting_html

    html_out, n = re.subn(
        r"(<body[^>]*>)",
        inject_after_body_open,
        html_body,
        count=1,
        flags=re.IGNORECASE,
    )
    if n:
        return md_out, html_out

    return md_out, greeting_html + html_body
