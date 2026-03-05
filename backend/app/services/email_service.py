"""Email service — sends verification code emails via SMTP."""

import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib
from aiosmtplib import SMTPAuthenticationError

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _validate_smtp_settings() -> None:
    placeholders = {"your_password", "noreply@your-domain.com", "your-domain.com"}
    if (
        not settings.SMTP_SERVER
        or not settings.SMTP_USER
        or not settings.SMTP_PASSWORD
        or settings.SMTP_USER in placeholders
        or settings.SMTP_PASSWORD in placeholders
        or "your-domain.com" in settings.SMTP_USER
    ):
        raise RuntimeError(
            "SMTP 配置未完成。请在 backend/.env 中设置真实的 SMTP_SERVER、SMTP_USER、SMTP_PASSWORD。"
        )


def _smtp_transport_options() -> dict:
    use_tls = settings.SMTP_USE_TLS
    start_tls = settings.SMTP_START_TLS

    # If the user did not override transport mode, infer a safe default from the port.
    if settings.SMTP_PORT == 465 and not start_tls:
        use_tls = True
    elif settings.SMTP_PORT in (587, 25) and not use_tls:
        start_tls = True

    return {
        "use_tls": use_tls,
        "start_tls": start_tls,
    }


async def send_verification_email(to_email: str, code: str, purpose: str) -> bool:
    """Send a verification code email.  Returns True on success."""
    _validate_smtp_settings()

    subject_map = {
        "register": "MediCode — 邮箱注册验证码",
        "reset-password": "MediCode — 重置密码验证码",
        "change-password": "MediCode — 修改密码验证码",
    }
    subject = subject_map.get(purpose, "MediCode — 验证码")

    html = f"""
    <div style="max-width:480px;margin:0 auto;font-family:sans-serif;color:#333;">
        <div style="text-align:center;padding:24px 0;">
            <h2 style="color:#059669;margin:0;">MediCode</h2>
            <p style="color:#888;font-size:13px;">专业医学统计分析平台</p>
        </div>
        <div style="background:#f8faf9;border-radius:12px;padding:32px;text-align:center;">
            <p style="font-size:15px;margin:0 0 20px;">您的验证码是：</p>
            <div style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#059669;
                        background:#fff;border:2px solid #d1fae5;border-radius:8px;
                        display:inline-block;padding:12px 32px;">
                {code}
            </div>
            <p style="font-size:13px;color:#888;margin:20px 0 0;">
                验证码 10 分钟内有效，请勿泄露给他人。
            </p>
        </div>
        <p style="text-align:center;font-size:11px;color:#bbb;margin-top:24px;">
            如果这不是您本人的操作，请忽略此邮件。
        </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        transport_options = _smtp_transport_options()
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            timeout=20,
            **transport_options,
        )
        logger.info("Verification email sent to %s (purpose=%s)", to_email, purpose)
        return True
    except SMTPAuthenticationError as e:
        logger.error(
            "SMTP authentication failed for %s via %s:%s: %s",
            settings.SMTP_USER,
            settings.SMTP_SERVER,
            settings.SMTP_PORT,
            e,
        )
        logger.error(
            "Check backend/.env SMTP settings. For QQ enterprise mail usually use port 465 with a valid mailbox password or app password."
        )
        return False
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        return False
