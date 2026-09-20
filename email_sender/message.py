import csv
import mimetypes
import re
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RecipientError(Exception):
    pass


@dataclass(frozen=True)
class Recipient:
    email: str
    fields: dict[str, str] = field(default_factory=dict)

    @property
    def context(self) -> dict[str, str]:
        return {"email": self.email, **self.fields}


def is_valid_email(address: str) -> bool:
    return bool(EMAIL_RE.match(address.strip()))


def load_recipients(path: Path) -> list[Recipient]:
    """Read recipients from a CSV file.

    The file may either have a header row containing an ``email`` column
    (any other columns become template fields) or be a single column of
    addresses without a header.
    """
    with open(path, newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.reader(handle) if any(cell.strip() for cell in row)]

    if not rows:
        raise RecipientError(f"No recipients found in {path}")

    header = [cell.strip().lower() for cell in rows[0]]
    recipients: list[Recipient] = []
    if "email" in header:
        index = header.index("email")
        for row in rows[1:]:
            address = row[index].strip() if index < len(row) else ""
            if not address:
                continue
            fields = {
                name: (row[i].strip() if i < len(row) else "")
                for i, name in enumerate(header)
                if i != index and name
            }
            recipients.append(Recipient(address, fields))
    else:
        for row in rows:
            address = row[0].strip()
            if address:
                recipients.append(Recipient(address))

    invalid = [r.email for r in recipients if not is_valid_email(r.email)]
    if invalid:
        raise RecipientError("Invalid email addresses: " + ", ".join(invalid))
    if not recipients:
        raise RecipientError(f"No recipients found in {path}")
    return recipients


def render(template: str, context: dict[str, str]) -> str:
    """Replace ``{{ field }}`` placeholders with values from ``context``."""
    return PLACEHOLDER.sub(lambda m: context.get(m.group(1), m.group(0)), template)


def build_message(
    *,
    subject: str,
    from_address: str,
    recipient: Recipient,
    text: str,
    html: str | None = None,
    attachments: list[Path] | None = None,
    reply_to: str | None = None,
) -> EmailMessage:
    context = recipient.context
    message = EmailMessage()
    message["Subject"] = render(subject, context)
    message["From"] = from_address
    message["To"] = recipient.email
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(render(text, context))
    if html:
        message.add_alternative(render(html, context), subtype="html")

    for attachment in attachments or []:
        mime_type, _ = mimetypes.guess_type(attachment.name)
        maintype, _, subtype = (mime_type or "application/octet-stream").partition("/")
        message.add_attachment(
            attachment.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=attachment.name,
        )
    return message
