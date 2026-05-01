from __future__ import annotations

import aiohttp
from app.settings import settings


async def send_reset_email(to: str, token: str) -> None:
    link = f"{settings.APP_SCHEME}://reset-password?token={token}"

    html = f"""
    <p>Для сброса пароля в BZ CRM нажмите на кнопку ниже.</p>
    <p>Ссылка действует 30 минут.</p>
    <p><a href="{link}">Сбросить пароль</a></p>
    <p style="color: #888; font-size: 12px;">
        Если вы не запрашивали сброс пароля — просто проигнорируйте это письмо.
    </p>
    """

    async with aiohttp.ClientSession() as session:
        async with session.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.SMTP_PASSWORD}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.SMTP_FROM,
                    "to": [to],
                    "subject": "Сброс пароля BZ CRM",
                    "html": html,  # ← вместо "text"
                },
        ) as response:
            if response.status >= 400:
                text = await response.text()
                raise RuntimeError(f"Resend error {response.status}: {text}")