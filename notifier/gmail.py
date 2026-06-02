"""
Gmail通知モジュール。
smtplib (Gmailアプリパスワード) を使用してメール送信。
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT
from notifier.gmail_mcp import build_report_email, build_hot_alert_email

logger = logging.getLogger(__name__)


def _smtp_send(subject: str, plain_body: str, html_body: str) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail認証情報が未設定のためSMTP送信をスキップ (.envを確認してください)")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        logger.info(f"メール送信成功: {GMAIL_RECIPIENT}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証失敗。アプリパスワードを確認してください。")
        return False
    except Exception as e:
        logger.error(f"メール送信失敗: {e}")
        return False


def send_daily_report(airdrops: list[dict], new_items: list[str], trending: list[dict], summary: dict | None = None) -> bool:
    subject, plain_body, html_body = build_report_email(airdrops, new_items, trending, summary)
    return _smtp_send(subject, plain_body, html_body)


def send_hot_alert(airdrop: dict) -> bool:
    subject, plain_body, html_body = build_hot_alert_email(airdrop)
    return _smtp_send(subject, plain_body, html_body)
