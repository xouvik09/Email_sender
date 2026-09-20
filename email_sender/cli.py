import argparse
import logging
import sys
from pathlib import Path

from email_sender.config import ConfigError, SMTPConfig
from email_sender.message import TemplateError
from email_sender.recipients import Recipient, RecipientError, read_recipients
from email_sender.sender import EmailSender

DEFAULT_CSV = "src/email.csv"
DEFAULT_HTML = "src/msg.html"
DEFAULT_TEXT = "src/msg.txt"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="email-sender",
        description="Send templated plaintext/HTML emails over SMTP.",
    )
    parser.add_argument("--csv", default=DEFAULT_CSV, help="CSV file of recipients")
    parser.add_argument("--to", action="append", default=[], help="Recipient address (repeatable)")
    parser.add_argument("--subject", default="Test Subject", help="Subject line template")
    parser.add_argument("--html", default=DEFAULT_HTML, help="HTML body template file")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Plaintext body template file")
    parser.add_argument(
        "--attach", action="append", default=[], help="File to attach (repeatable)"
    )
    parser.add_argument("--env-file", default=None, help="Path to a .env file")
    parser.add_argument(
        "--delay", type=float, default=0.0, help="Seconds to wait between messages"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render and validate everything without connecting to the SMTP server",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def _read_body(path: str | None, required: bool) -> str | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.is_file():
        if required:
            raise FileNotFoundError(f"Body template not found: {file_path}")
        return None
    return file_path.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    try:
        if args.to:
            recipients = [Recipient(email=address) for address in args.to]
        else:
            recipients = read_recipients(args.csv)

        text_body = _read_body(args.text, required=True) or ""
        html_body = _read_body(args.html, required=False)

        if args.dry_run:
            config = SMTPConfig(host="dry-run", username="dry-run@example.com", password="")
        else:
            config = SMTPConfig.from_env(args.env_file)
    except (ConfigError, RecipientError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        with EmailSender(config, dry_run=args.dry_run, delay=args.delay) as sender:
            results = sender.send_batch(
                recipients=recipients,
                subject=args.subject,
                text_body=text_body,
                html_body=html_body,
                attachments=args.attach,
            )
    except (OSError, TemplateError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    failures = [result for result in results if not result.sent]
    verb = "would send" if args.dry_run else "sent"
    print(f"{verb} {len(results) - len(failures)}/{len(results)} messages")
    for failure in failures:
        print(f"  failed: {failure.recipient}: {failure.error}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
