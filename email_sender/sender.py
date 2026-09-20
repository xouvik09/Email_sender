import logging
import smtplib
import ssl
import time
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from types import TracebackType

from email_sender.config import SMTPConfig
from email_sender.message import TemplateError, build_message
from email_sender.recipients import Recipient

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    recipient: str
    sent: bool
    error: str = ""


class EmailSender:
    """Sends messages over SMTP, reusing a single connection for the batch."""

    def __init__(
        self,
        config: SMTPConfig,
        dry_run: bool = False,
        delay: float = 0.0,
        timeout: float = 30.0,
    ) -> None:
        self.config = config
        self.dry_run = dry_run
        self.delay = delay
        self.timeout = timeout
        self._server: smtplib.SMTP | None = None

    def __enter__(self) -> "EmailSender":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def connect(self) -> None:
        if self.dry_run or self._server is not None:
            return
        context = ssl.create_default_context()
        if self.config.use_ssl:
            server: smtplib.SMTP = smtplib.SMTP_SSL(
                self.config.host, self.config.port, context=context, timeout=self.timeout
            )
        else:
            server = smtplib.SMTP(self.config.host, self.config.port, timeout=self.timeout)
            server.starttls(context=context)
        server.login(self.config.username, self.config.password)
        self._server = server

    def close(self) -> None:
        if self._server is None:
            return
        try:
            self._server.quit()
        except smtplib.SMTPException:
            logger.debug("SMTP server did not accept QUIT cleanly", exc_info=True)
        finally:
            self._server = None

    def send_message(self, message: EmailMessage) -> None:
        if self.dry_run:
            return
        if self._server is None:
            self.connect()
        assert self._server is not None
        self._server.send_message(message)

    def send_batch(
        self,
        recipients: list[Recipient],
        subject: str,
        text_body: str,
        html_body: str | None = None,
        attachments: list[str | Path] | None = None,
    ) -> list[SendResult]:
        results: list[SendResult] = []
        for index, recipient in enumerate(recipients):
            try:
                message = build_message(
                    subject=subject,
                    sender=self.config.from_address,
                    recipient=recipient.email,
                    text_body=text_body,
                    html_body=html_body,
                    context=recipient.context,
                    attachments=attachments,
                )
                self.send_message(message)
                results.append(SendResult(recipient=recipient.email, sent=True))
                logger.info(
                    "%s %s", "would send to" if self.dry_run else "sent to", recipient.email
                )
            except (smtplib.SMTPException, OSError, TemplateError) as exc:
                results.append(SendResult(recipient=recipient.email, sent=False, error=str(exc)))
                logger.error("failed to send to %s: %s", recipient.email, exc)

            if self.delay and not self.dry_run and index < len(recipients) - 1:
                time.sleep(self.delay)

        return results
