# app/core/email_utils.py
from email.message import EmailMessage
from aiosmtplib import send
from app.core.config import get_settings

settings = get_settings()


async def send_email(subject: str, to_email: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    await send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )
