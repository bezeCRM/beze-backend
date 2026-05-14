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

<body style="margin:0; padding:0; background:#f7f4f6; font-family:Arial, Helvetica, sans-serif; color:#111111;">
  <div style="display:none; max-height:0; overflow:hidden; opacity:0; color:transparent;">
    Восстановление доступа к аккаунту bezeCRM
  </div>

  <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#f7f4f6; padding:28px 14px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="max-width:560px;">
          <tr>
            <td align="center" style="padding:10px 0 24px;">
              <table cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td style="vertical-align:middle;">
                    <div style="width:38px; height:38px; border:2px solid #fb7faa; border-radius:12px; color:#fb7faa; font-size:24px; line-height:38px; font-weight:700; font-family:Georgia, serif; text-align:center;">
                      B
                    </div>
                  </td>
                  <td style="padding-left:10px; vertical-align:middle;">
                    <div style="font-size:26px; line-height:30px; font-weight:800; color:#090909; letter-spacing:-0.5px;">
                      bezeCRM
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td style="background:#ffffff; border-radius:28px; overflow:hidden; box-shadow:0 14px 40px rgba(20, 20, 20, 0.08);">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td style="padding:34px 30px 18px;">
                    <div style="display:inline-block; padding:8px 14px; border-radius:999px; background:#fff0f6; color:#fb7faa; font-size:13px; line-height:18px; font-weight:700;">
                      Восстановление доступа
                    </div>

                    <h1 style="margin:22px 0 0; font-size:30px; line-height:36px; font-weight:800; color:#090909; letter-spacing:-0.6px;">
                      Сброс пароля
                    </h1>

                    <p style="margin:14px 0 0; font-size:16px; line-height:24px; color:#333333;">
                      Вы запросили восстановление доступа к аккаунту bezeCRM.
                    </p>

                    <p style="margin:10px 0 0; font-size:16px; line-height:24px; color:#333333;">
                      Нажмите на кнопку ниже, чтобы открыть приложение и создать новый пароль.
                    </p>
                  </td>
                </tr>

                <tr>
                  <td style="padding:8px 30px 10px;">
                    <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#fb7faa; border-radius:18px;">
                      <tr>
                        <td align="center" style="padding:16px 20px;">
                          <a href="{safe_link}" target="_blank" style="display:block; color:#ffffff; font-size:17px; line-height:22px; font-weight:800; text-decoration:none;">
                            Сбросить пароль
                          </a>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td style="padding:14px 30px 26px;">
                    <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#fafafa; border-radius:20px;">
                      <tr>
                        <td style="padding:18px 18px 16px;">
                          <div style="font-size:14px; line-height:20px; font-weight:800; color:#111111;">
                            Ссылка действует 30 минут
                          </div>

                          <p style="margin:6px 0 0; font-size:14px; line-height:21px; color:#686868;">
                            Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо. Ваш аккаунт останется в безопасности.
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td style="padding:0 30px 32px;">
                    <div style="height:1px; background:#f0edf0; margin-bottom:18px;"></div>

                    <p style="margin:0 0 8px; font-size:12px; line-height:18px; color:#9a9a9a;">
                      Если кнопка не работает, скопируйте ссылку и откройте ее на устройстве с установленным приложением:
                    </p>

                    <p style="margin:0; font-size:12px; line-height:18px; color:#777777; word-break:break-all;">
                      <a href="{safe_link}" target="_blank" style="color:#fb7faa; text-decoration:underline;">
                        {safe_link}
                      </a>
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td align="center" style="padding:18px 18px 0;">
              <p style="margin:0; font-size:12px; line-height:18px; color:#aaa6aa;">
                bezeCRM · заботливо для кондитеров
              </p>
            </td>
          </tr>
        </table>
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