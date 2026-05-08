"""Phase 5 runner: create email draft (.eml) or send the pulse."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings  # noqa: E402
from phase5_email.delivery import deliver_pulse_email, send_transport_available  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 5 — draft (.eml), send (Resend or SMTP), or both"
    )
    parser.add_argument("--pulse-json", required=True, help="Path to pulse_<run_id>.json")
    parser.add_argument("--pulse-md", required=True, help="Path to pulse_<run_id>.md")
    parser.add_argument("--pulse-html", required=True, help="Path to pulse_<run_id>.html")
    parser.add_argument(
        "--mode",
        choices=["draft", "send", "both"],
        default=settings.email_mode,
        help="draft=write .eml only; send=deliver mail; both=draft then send",
    )
    parser.add_argument(
        "--recipient",
        default=None,
        help="To address (same as future frontend). Defaults to ALERT_EMAIL if set.",
    )
    parser.add_argument(
        "--sender",
        default=None,
        help="Optional From override for local testing; production should use EMAIL_FROM env.",
    )
    parser.add_argument(
        "--recipient-name",
        "--name",
        dest="recipient_name",
        default=None,
        metavar="NAME",
        help='Greeting name (e.g. "Jane"); produces Hi Jane, at the top of the email.',
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
    )

    effective_mode = args.mode
    if effective_mode == "both" and not send_transport_available(settings):
        raise RuntimeError(
            "Mode 'both' requires RESEND_API_KEY or SMTP_USER + SMTP_PASS in .env. "
            "Use --mode draft to only write the .eml file."
        )
    if effective_mode == "send" and not send_transport_available(settings):
        raise RuntimeError(
            "Send mode needs RESEND_API_KEY or SMTP_USER + SMTP_PASS. "
            "Configure one of these, or use --mode draft."
        )

    p_json = Path(args.pulse_json)
    p_md = Path(args.pulse_md)
    p_html = Path(args.pulse_html)

    try:
        result = deliver_pulse_email(
            pulse_json=p_json,
            pulse_md=p_md,
            pulse_html=p_html,
            mode=effective_mode,
            recipient=args.recipient,
            recipient_name=args.recipient_name,
            sender_override=args.sender,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print()
    if effective_mode == "draft":
        print("Phase 5 complete (draft mode)")
        print("-----------------------------")
        print(f"Pulse JSON: {result.pulse_json}")
        print(f"Draft EML:  {result.draft_eml_path}")
        print(f"Log CSV:    {result.log_path}")
    elif effective_mode == "send":
        print("Phase 5 complete (send mode)")
        print("----------------------------")
        print(f"Pulse JSON: {result.pulse_json}")
        print(f"Channel:    {result.send_channel}")
        print(f"Log CSV:    {result.log_path}")
    else:
        print("Phase 5 complete (draft + send)")
        print("-------------------------------")
        print(f"Pulse JSON: {result.pulse_json}")
        print(f"Draft EML:  {result.draft_eml_path}")
        print(f"Channel:    {result.send_channel}")
        print(f"Log CSV:    {result.log_path}")
    print(f"Recipient:  {result.recipient}")
    print(f"Sender:     {result.sender}")
    if result.recipient_display_name:
        print(f"Greeting:   Hi {result.recipient_display_name},")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
