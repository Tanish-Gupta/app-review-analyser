# Phase 5 — Email Draft / Send

Two modes:

- **`draft`** — writes a `.eml` file into `data/output/`.
- **`send`** — uses Resend API if `RESEND_API_KEY` exists, otherwise SMTP fallback.

The HTML part of draft/send uses a **separate email layout** (`phase5_email/src/email_html.py`): gradient hero, 600px card shell, scoped typography — **without changing** the Phase 4 `pulse_*.html` files on disk.

Also appends to `data/output/email_log.csv`.

## Recipient and From (frontend API later)

- **Recipient (`To`)** — supplied per action from the UI/API (`recipient` argument to `deliver_pulse_email`). CLI defaults to `ALERT_EMAIL` if `--recipient` is omitted.
- **Sender (`From`)** — **never** taken from the browser; set **`EMAIL_FROM`** (preferred) or **`ALERT_EMAIL`** as fallback for the envelope sender. Optional `--sender` is only for local testing.
- **Greeting name** — optional **`recipient_name`** (from the UI) inserts `Hi <name>,` above the pulse in both plain-text and HTML.

Import from Python (Phase 6 serverless / routes):

```python
from phase5_email import deliver_pulse_email

deliver_pulse_email(
    pulse_json=path_to_pulse_json,
    pulse_md=path_to_md,
    pulse_html=path_to_html,
    mode="send",
    recipient=request_body["email"],
    recipient_name=request_body.get("name"),  # e.g. "Jane"
)
```

## Run

```bash
python -m phase5_email.run \
  --pulse-json data/output/pulse_<run_id>.json \
  --pulse-md data/output/pulse_<run_id>.md \
  --pulse-html data/output/pulse_<run_id>.html \
  --recipient-name "Jane" \
  --mode draft
```
