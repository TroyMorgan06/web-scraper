"""Email alerts when a tracked product price changes."""

import smtplib
from email.message import EmailMessage

from app import config


def email_configured() -> bool:
    """True only if we have enough settings to send mail."""
    return bool(config.SMTP_USER and config.SMTP_PASSWORD and config.ALERT_EMAIL)


def send_price_alert(title, url: str, old_price, new_price) -> bool:
    """Send a price-change email. Returns True if sent, False if skipped."""
    if not email_configured():
        print(
            "Skipping email alert: set SMTP_USER, SMTP_PASSWORD, "
            "and ALERT_EMAIL in a .env file."
        )
        return False

    product_name = title or url
    msg = EmailMessage()
    msg["Subject"] = f"Price change: {product_name}"
    msg["From"] = config.SMTP_USER
    msg["To"] = config.ALERT_EMAIL
    msg.set_content(
        f"Product: {product_name}\n"
        f"URL: {url}\n"
        f"Old price: {old_price}\n"
        f"New price: {new_price}\n"
    )

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.send_message(msg)
        return True
