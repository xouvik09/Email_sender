import logging
import smtplib
import ssl
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from .config import SmtpConfig
from .message import Recipient, build_message

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    recipient: str
    sent: bool
    error: str = ""


@contextmanager
def open_connection(config: SmtpConfig) -> Iterator[smtplib.SMTP]:
    context = ssl.create_default_context()
    if config.use_ssl:
        server: smtplib.SMTP = smtplib.SMTP_SSL(
            config.host, config.port, context=context
        )
    else:
        server = smtplib.SMTP(config.host, config.port)
        server.starttls(context=context)
    try:
        server.login(config.username, config.password)
        yield server
    finally:
        try:
            server.quit()
        except smtplib.SMTPException:
            server.close()


def send_bulk(
    config: SmtpConfig,
    recipients: Sequence[Recipient],
    *,
    subject: str,
    text: str,
    html: str | None = None,
    attachments: list[Path] | None = None,
    reply_to: str | None = None,
    dry_run: bool = False,
    delay: float = 0.0,
    retries: int = 1,
) -> list[SendResult]:
    """Send one personalized message per recipient over a single connection."""
    messages: list[tuple[Recipient, EmailMessage]] = [
        (
            recipient,
            build_message(
                subject=subject,
                from_address=config.from_address,
                recipient=recipient,
                text=text,
                html=html,
                attachments=attachments,
                reply_to=reply_to,
            ),
        )
        for recipient in recipients
    ]

    if dry_run:
        for recipient, message in messages:
            logger.info(
                "[dry-run] would send to %s: %s", recipient.email, message["Subject"]
            )
        return [SendResult(recipient.email, True) for recipient, _ in messages]

    results: list[SendResult] = []
    with open_connection(config) as server:
        for index, (recipient, message) in enumerate(messages):
            results.append(_send_one(server, config, recipient, message, retries))
            if delay and index < len(messages) - 1:
                time.sleep(delay)
    return results


def _send_one(
    server: smtplib.SMTP,
    config: SmtpConfig,
    recipient: Recipient,
    message: EmailMessage,
    retries: int,
) -> SendResult:
    last_error = ""
    for attempt in range(1, max(retries, 1) + 1):
        try:
            server.send_message(
                message, from_addr=config.envelope_from, to_addrs=[recipient.email]
            )
            logger.info("Sent to %s", recipient.email)
            return SendResult(recipient.email, True)
        except smtplib.SMTPException as exc:
            last_error = str(exc)
            logger.warning(
                "Attempt %s/%s failed for %s: %s",
                attempt,
                max(retries, 1),
                recipient.email,
                last_error,
            )
    return SendResult(recipient.email, False, last_error)
