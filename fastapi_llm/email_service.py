import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY", "")
FROM_ADDRESS = "Acme <onboarding@resend.dev>"


def build_email_html(guest_name: str, event_name: str, event_date: str = "") -> str:
    date_line = f'<p style="margin:0 0 24px;color:#94a3b8;font-size:14px;">📅 {event_date}</p>' if event_date else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#0f172a;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f172a;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);border-radius:16px;border:1px solid rgba(255,255,255,0.08);overflow:hidden;">

        <tr><td style="padding:32px 40px 24px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.06);">
          <h1 style="margin:0;font-size:28px;font-weight:700;letter-spacing:-0.5px;">
            <span style="background:linear-gradient(135deg,#60a5fa,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Planorama</span>
            <span style="font-size:22px;"> ✨</span>
          </h1>
          <p style="margin:8px 0 0;color:#64748b;font-size:13px;text-transform:uppercase;letter-spacing:2px;">Event Planning Assistant</p>
        </td></tr>

        <tr><td style="padding:36px 40px;">
          <p style="margin:0 0 20px;color:#f8fafc;font-size:18px;font-weight:600;">Hi {guest_name} 👋</p>
          <p style="margin:0 0 24px;color:#cbd5e1;font-size:15px;line-height:1.7;">
            We're reaching out regarding <strong style="color:#f8fafc;">{event_name}</strong>. We'd love to make sure everything is on track and you have all the details you need.
          </p>
          {date_line}
          <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
            <tr>
              <td style="background:linear-gradient(135deg,#3b82f6,#8b5cf6);border-radius:9999px;padding:12px 32px;">
                <span style="color:#ffffff;font-size:14px;font-weight:600;text-decoration:none;">Please Update Your RSVP</span>
              </td>
            </tr>
          </table>
          <p style="margin:0;color:#94a3b8;font-size:14px;line-height:1.6;">
            If you have any questions or need to make changes, simply reply to this email or contact your event planner.
          </p>
        </td></tr>

        <tr><td style="padding:24px 40px 32px;border-top:1px solid rgba(255,255,255,0.06);text-align:center;">
          <p style="margin:0 0 4px;color:#64748b;font-size:12px;">Sent with 💜 by Planorama</p>
          <p style="margin:0;color:#475569;font-size:11px;">AI-powered event planning</p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_email(to: str, subject: str, guest_name: str, event_name: str, event_date: str = "") -> dict:
    try:
        html_body = build_email_html(guest_name, event_name, event_date)
        params: resend.Emails.SendParams = {
            "from": FROM_ADDRESS,
            "to": ["delivered@resend.dev"],
            "subject": subject,
            "html": html_body,
        }
        print(f"[EMAIL] Sending email for guest '{guest_name}' (original to: {to}) -> delivered@resend.dev")
        result = resend.Emails.send(params)
        msg_id = result.get("id", "") if isinstance(result, dict) else getattr(result, "id", "")
        print(f"[EMAIL] Success! Message ID: {msg_id}")
        return {"success": True, "id": msg_id, "error": None}
    except Exception as e:
        print(f"[EMAIL] Failed: {str(e)}")
        return {"success": False, "id": None, "error": str(e)}
