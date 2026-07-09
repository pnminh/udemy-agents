import os
import smtplib
from email.message import EmailMessage

from crewai.tools import tool

from stock_picker.env import load_project_env


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is not set in environment")
    return value


@tool("Send HTML Email")
def send_html_email(subject: str, html_body: str, recipient: str = "") -> str:
    """Send an HTML email via SMTP using SMTP_SERVER_* vars from the repo-root .env.

    Args:
        subject: Email subject line.
        html_body: HTML content for the email body.
        recipient: Recipient email address. Defaults to SMTP_SERVER_EMAIL.

    Returns:
        Confirmation message after the email is sent.
    """
    load_project_env()

    host = _require_env("SMTP_SERVER_URL")
    port = int(_require_env("SMTP_SERVER_PORT"))
    username = _require_env("SMTP_SERVER_USERNAME")
    password = _require_env("SMTP_SERVER_PASSWORD")
    from_addr = _require_env("SMTP_SERVER_EMAIL")
    to_addr = recipient.strip() or from_addr

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_addr
    message["To"] = to_addr
    message.set_content(
        "Please view this email in an HTML-capable email client.",
        subtype="plain",
        charset="utf-8",
    )
    message.add_alternative(html_body, subtype="html", charset="utf-8")

    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=45) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=45) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(message)

    return f"HTML email sent to {to_addr} with subject: {subject!r}"
