import argparse
import logging
import smtplib
import sys
from pathlib import Path

from .config import ConfigError, SmtpConfig, load_dotenv
from .message import Recipient, RecipientError, load_recipients
from .sender import send_bulk


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="email-sender",
        description="Send personalized plaintext/HTML emails over SMTP.",
    )
    parser.add_argument("--subject", default="Hello from Email Sender")
    parser.add_argument(
        "--to", action="append", default=[], help="Recipient address (repeatable)"
    )
    parser.add_argument("--csv", type=Path, help="CSV file with recipients")
    parser.add_argument("--text", type=Path, default=Path("src/msg.txt"))
    parser.add_argument("--html", type=Path, default=Path("src/msg.html"))
    parser.add_argument(
        "--attach", action="append", type=Path, default=[], help="File to attach"
    )
    parser.add_argument("--reply-to")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument(
        "--delay", type=float, default=0.0, help="Seconds to wait between messages"
    )
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def collect_recipients(args: argparse.Namespace) -> list[Recipient]:
    recipients = [Recipient(address) for address in args.to]
    if args.csv:
        recipients.extend(load_recipients(args.csv))
    if not recipients:
        raise RecipientError("No recipients: pass --to and/or --csv")
    return recipients


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    load_dotenv(args.env_file)
    try:
        config = SmtpConfig.from_env()
        recipients = collect_recipients(args)
    except (ConfigError, RecipientError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not args.text.is_file():
        print(f"error: text body not found: {args.text}", file=sys.stderr)
        return 2
    text = args.text.read_text(encoding="utf-8")
    html = args.html.read_text(encoding="utf-8") if args.html.is_file() else None

    missing = [str(path) for path in args.attach if not path.is_file()]
    if missing:
        print("error: attachment not found: " + ", ".join(missing), file=sys.stderr)
        return 2

    try:
        results = send_bulk(
            config,
            recipients,
            subject=args.subject,
            text=text,
            html=html,
            attachments=args.attach,
            reply_to=args.reply_to,
            dry_run=args.dry_run,
            delay=args.delay,
            retries=args.retries,
        )
    except (smtplib.SMTPException, OSError) as exc:
        print(
            f"error: could not connect to {config.host}:{config.port}: {exc}",
            file=sys.stderr,
        )
        return 3

    failures = [result for result in results if not result.sent]
    print(f"{len(results) - len(failures)}/{len(results)} messages sent")
    for failure in failures:
        print(f"failed: {failure.recipient}: {failure.error}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
