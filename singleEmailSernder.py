"""Single plaintext email sending, kept for backwards compatibility.

Configuration now comes from the environment (see .env.example); equivalent to:
    python -m email_sender.cli --to someone@example.com --text src/msg.txt --html ""
"""

import sys

from email_sender.cli import main

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "usage: python singleEmailSernder.py recipient@example.com", file=sys.stderr
        )
        raise SystemExit(2)
    raise SystemExit(
        main(
            [
                "--to",
                sys.argv[1],
                "--text",
                "src/msg.txt",
                "--html",
                "src/msg.html",
                *sys.argv[2:],
            ]
        )
    )
