import argparse
import os

from email_sender.web.app import create_app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="email-sender-web", description="Serve the Email Sender web UI."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    parser.add_argument(
        "--dry-run-only",
        action="store_true",
        help="Refuse to send for real; every request is treated as a dry run",
    )
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    create_app(dry_run_only=args.dry_run_only).run(
        host=args.host, port=args.port, debug=args.debug
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
