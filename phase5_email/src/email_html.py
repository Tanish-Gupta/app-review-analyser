"""Wrap the Phase 4 pulse HTML in a responsive, email-client-friendly shell."""

from __future__ import annotations

import html as html_module
import re


def extract_body_inner(document_html: str) -> str:
    """Return the contents of ``<body>...</body>``, or the whole string if missing."""
    m = re.search(r"<body[^>]*>(.*)</body>", document_html, re.IGNORECASE | re.DOTALL)
    if not m:
        return document_html.strip()
    return m.group(1).strip()


def strip_first_h1(fragment: str) -> str:
    """Remove the first ``<h1>...</h1>`` so the hero header does not duplicate the title."""
    return re.sub(r"<h1[^>]*>.*?</h1>", "", fragment, count=1, flags=re.IGNORECASE | re.DOTALL).strip()


def apply_fancy_email_shell(html_body: str, *, document_title: str) -> str:
    """Wrap pulse HTML in a polished layout suitable for SMTP / Resend HTML parts."""
    inner = extract_body_inner(html_body)
    inner = strip_first_h1(inner)
    title_esc = html_module.escape(document_title)

    # Inner HTML is concatenated raw so review text cannot break templating ($, braces).
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en" xmlns="http://www.w3.org/1999/xhtml">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<meta http-equiv="X-UA-Compatible" content="IE=edge">\n'
        f"<title>{title_esc}</title>\n"
        "<!--[if mso]>\n"
        "<noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>\n"
        "<![endif]-->\n"
        '<style type="text/css">\n'
        "  body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }\n"
        "  table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; }\n"
        "  img { -ms-interpolation-mode: bicubic; border: 0; outline: none; text-decoration: none; }\n"
        "  body { margin: 0 !important; padding: 0 !important; width: 100% !important; }\n"
        "  .pulse-email h2 {\n"
        "    font-family: Georgia, 'Times New Roman', serif;\n"
        "    font-size: 18px;\n"
        "    color: #14524f;\n"
        "    margin: 28px 0 14px 0;\n"
        "    border-bottom: 2px solid #c5ddd9;\n"
        "    padding-bottom: 8px;\n"
        "  }\n"
        "  .pulse-email .meta {\n"
        "    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;\n"
        "    font-size: 13px;\n"
        "    color: #5a6f6d;\n"
        "    margin-bottom: 20px;\n"
        "    line-height: 1.5;\n"
        "  }\n"
        "  .pulse-email .card {\n"
        "    background: #fafcfb;\n"
        "    border: 1px solid #d4e5e2;\n"
        "    border-radius: 10px;\n"
        "    padding: 16px 18px;\n"
        "    margin: 0 0 12px 0;\n"
        "    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;\n"
        "    font-size: 14px;\n"
        "    color: #1a2e2c;\n"
        "    line-height: 1.55;\n"
        "  }\n"
        "  .pulse-email ul, .pulse-email ol {\n"
        "    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;\n"
        "    font-size: 14px;\n"
        "    color: #2c3d3b;\n"
        "    line-height: 1.55;\n"
        "    padding-left: 22px;\n"
        "    margin: 12px 0;\n"
        "  }\n"
        "  .pulse-email li { margin-bottom: 10px; }\n"
        "  .pulse-email p.greeting {\n"
        "    font-family: Georgia, 'Times New Roman', serif;\n"
        "    font-size: 20px;\n"
        "    color: #0d4f4f;\n"
        "    margin: 0 0 22px 0;\n"
        "    line-height: 1.35;\n"
        "  }\n"
        "</style>\n"
        "</head>\n"
        '<body style="margin:0;padding:0;background-color:#e8efed;">\n'
        '  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#e8efed;">\n'
        "    <tr>\n"
        '      <td align="center" style="padding: 24px 16px 40px 16px;">\n'
        '        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="max-width:600px;width:100%;background-color:#ffffff;border-radius:12px;overflow:hidden;border-collapse:separate;box-shadow:0 10px 40px rgba(13,79,79,0.14);">\n'
        "          <tr>\n"
        '            <td style="background-color:#0a3d3a;background-image:linear-gradient(135deg,#062e2c 0%,#147a72 48%,#1a9588 100%);padding:28px 32px 26px 32px;text-align:left;">\n'
        '              <div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.72);margin-bottom:10px;">Review intelligence</div>\n'
        '              <div style="width:44px;height:3px;background-color:#e8c547;border-radius:2px;margin-bottom:14px;"></div>\n'
        f'              <div style="font-family:Georgia,\'Times New Roman\',serif;font-size:22px;font-weight:700;color:#ffffff;line-height:1.28;text-shadow:0 1px 2px rgba(0,0,0,0.18);">{title_esc}</div>\n'
        "            </td>\n"
        "          </tr>\n"
        "          <tr>\n"
        '            <td style="padding:32px 32px 36px 32px;" class="pulse-email">\n'
        f"{inner}\n"
        "            </td>\n"
        "          </tr>\n"
        "          <tr>\n"
        '            <td style="background:#f4f8f7;padding:20px 32px;border-top:1px solid #d4e5e2;text-align:center;">\n'
        '              <p style="margin:0;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;font-size:11px;color:#7a9190;line-height:1.55;">\n'
        "                Groww Weekly Pulse · synthesized from Play Store reviews\n"
        "              </p>\n"
        "            </td>\n"
        "          </tr>\n"
        "        </table>\n"
        "      </td>\n"
        "    </tr>\n"
        "  </table>\n"
        "</body>\n"
        "</html>\n"
    )
