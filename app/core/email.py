from __future__ import annotations

from html import escape
from urllib.parse import quote

import aiohttp

from app.settings import settings


RESEND_API_URL = "https://api.resend.com/emails"


def build_reset_password_link(token: str) -> str:
    safe_token = quote(token, safe="")

    return f"https://bezecrm.ru/auth/reset-password?token={safe_token}"


def build_reset_password_email_html(link: str) -> str:
    safe_link = escape(link, quote=True)

    return f"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Сброс пароля bezeCRM</title>
</head>
<body style="margin:0; padding:0; background:#f6f7fb; font-family:Arial, Helvetica, sans-serif; color:#1f2937;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#f6f7fb; padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="max-width:560px; background:#ffffff; border-radius:18px; overflow:hidden; box-shadow:0 8px 24px rgba(15, 23, 42, 0.08);">
          <tr>
            <td style="padding:32px 32px 20px;">
              <div style="font-size:24px; line-height:32px; font-weight:700; color:#111827;">
                Сброс пароля
              </div>

              <p style="margin:16px 0 0; font-size:16px; line-height:24px; color:#374151;">
                Вы запросили восстановление доступа к аккаунту bezeCRM.
              </p>

              <p style="margin:12px 0 0; font-size:16px; line-height:24px; color:#374151;">
                Нажмите на кнопку ниже, чтобы открыть приложение и создать новый пароль.
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding:8px 32px 28px;">
              <a href="{safe_link}" target="_blank" style="display:inline-block; padding:14px 22px; border-radius:12px; background:#111827; color:#ffffff; font-size:16px; line-height:20px; font-weight:700; text-decoration:none;">
                Сбросить пароль
              </a>
            </td>
          </tr>

          <tr>
            <td style="padding:0 32px 24px;">
              <p style="margin:0; font-size:14px; line-height:22px; color:#6b7280;">
                Ссылка действует 30 минут. Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding:20px 32px 32px; border-top:1px solid #eef0f4;">
              <p style="margin:0 0 8px; font-size:12px; line-height:18px; color:#9ca3af;">
                Если кнопка не работает, скопируйте эту ссылку и откройте ее на устройстве с установленным приложением:
              </p>

              <p style="margin:0; font-size:12px; line-height:18px; color:#6b7280; word-break:break-all;">
                <a href="{safe_link}" target="_blank" style="color:#374151; text-decoration:underline;">{safe_link}</a>
              </p>
            </td>
          </tr>
        </table>

        <p style="margin:18px 0 0; font-size:12px; line-height:18px; color:#9ca3af;">
          bezeCRM
        </p>
      </td>
    </tr>
  </table>
</body>
</html>
"""


async def send_reset_email(to: str, token: str) -> None:
    link = build_reset_password_link(token)
    html = build_reset_password_email_html(link)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        async with session.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {settings.SMTP_PASSWORD}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.SMTP_FROM,
                "to": [to],
                "subject": "Сброс пароля bezeCRM",
                "html": html,
            },
        ) as response:
            if response.status >= 400:
                text = await response.text()
                raise RuntimeError(f"Resend error {response.status}: {text}")