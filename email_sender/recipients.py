import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RecipientError(Exception):
    """Raised when a recipient list cannot be read."""


@dataclass(frozen=True)
class Recipient:
    email: str
    fields: dict[str, str] = field(default_factory=dict)

    @property
    def context(self) -> dict[str, str]:
        return {"email": self.email, **self.fields}


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value.strip()))


def read_recipients(path: str | Path, skip_invalid: bool = True) -> list[Recipient]:
    """Read recipients from a CSV file.

    The file may be a bare single column of addresses, or have a header row
    where one column is named ``email``; remaining columns become template
    variables for that recipient.
    """
    csv_path = Path(path)
    if not csv_path.is_file():
        raise RecipientError(f"Recipient file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.reader(handle) if any(cell.strip() for cell in row)]

    if not rows:
        raise RecipientError(f"Recipient file is empty: {csv_path}")

    header = [cell.strip().lower() for cell in rows[0]]
    if "email" in header:
        email_index = header.index("email")
        data_rows = rows[1:]
    else:
        email_index = 0
        header = []
        data_rows = rows

    recipients: list[Recipient] = []
    seen: set[str] = set()
    invalid: list[str] = []

    for row in data_rows:
        if email_index >= len(row):
            continue
        address = row[email_index].strip()
        if not is_valid_email(address):
            invalid.append(address)
            continue
        key = address.lower()
        if key in seen:
            continue
        seen.add(key)

        fields = {
            name: row[index].strip()
            for index, name in enumerate(header)
            if name and name != "email" and index < len(row)
        }
        recipients.append(Recipient(email=address, fields=fields))

    if invalid and not skip_invalid:
        raise RecipientError("Invalid email addresses: " + ", ".join(invalid))
    if not recipients:
        raise RecipientError(f"No valid email addresses found in {csv_path}")

    return recipients
