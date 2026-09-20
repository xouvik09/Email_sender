"""Bulk HTML email sending, kept for backwards compatibility.

Configuration now comes from the environment (see .env.example); equivalent to:
    python -m email_sender.cli --csv src/email.csv --text src/msg.txt --html src/msg.html
"""

import sys

from email_sender.cli import main

if __name__ == "__main__":
    raise SystemExit(
        main(
            [
                "--csv",
                "src/email.csv",
                "--text",
                "src/msg.txt",
                "--html",
                "src/msg.html",
                *sys.argv[1:],
            ]
        )
    )
