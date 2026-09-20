"""Send templated plaintext/HTML emails over SMTP to one or many recipients."""

from email_sender.config import SMTPConfig
from email_sender.message import build_message, render
from email_sender.recipients import Recipient, read_recipients
from email_sender.sender import EmailSender, SendResult

__all__ = [
    "EmailSender",
    "Recipient",
    "SMTPConfig",
    "SendResult",
    "build_message",
    "read_recipients",
    "render",
]
