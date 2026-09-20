# Email Sender

Python tool to send personalized plaintext + HTML emails over SMTP, to a single
address or in bulk from a CSV file.

- Credentials are read from the environment / `.env` (never hard-coded)
- Per-recipient personalization with `{{ field }}` placeholders from CSV columns
- Plaintext + HTML multipart bodies, file attachments, `Reply-To`
- One SMTP connection for the whole run, with retries, throttling and a `--dry-run` mode
- Per-recipient success/failure summary and a non-zero exit code on failures

## Installation

```bash
pip install -r requirements.txt   # only needed to run the tests; the tool itself is stdlib-only
cp .env.example .env              # then fill in your SMTP credentials
```

Gmail requires an [app password](https://support.google.com/accounts/answer/185833);
your normal account password will not work.

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `SMTP_HOST` | yes | – | e.g. `smtp.gmail.com` |
| `SMTP_USERNAME` | yes | – | Login user |
| `SMTP_PASSWORD` | yes | – | Login password / app password |
| `SMTP_PORT` | no | `465` (SSL) / `587` (STARTTLS) | Server port |
| `SMTP_USE_SSL` | no | `true` | `false` uses STARTTLS |
| `SMTP_SENDER` | no | `SMTP_USERNAME` | From address |
| `SMTP_SENDER_NAME` | no | – | Display name |

## Usage

```bash
# Single recipient
python -m email_sender.cli --to someone@example.com --subject "Hello"

# Bulk from CSV, with an attachment, 1s between messages
python -m email_sender.cli \
  --csv src/email.csv \
  --subject "Thanks, {{ name }}" \
  --text src/msg.txt --html src/msg.html \
  --attach invoice.pdf --delay 1

# Preview without connecting to the server
python -m email_sender.cli --csv src/email.csv --dry-run --verbose
```

Options: `--to` (repeatable), `--csv`, `--subject`, `--text`, `--html`, `--attach`
(repeatable), `--reply-to`, `--env-file`, `--delay`, `--retries`, `--dry-run`, `--verbose`.

### Recipients CSV

With a header row, `email` is the address and every other column becomes a
template field:

```csv
email,name
someone@example.com,Someone
```

A single column of addresses with no header also works. Invalid addresses abort
the run before anything is sent.

### Templates

`{{ field }}` placeholders in the subject, `src/msg.txt` and `src/msg.html` are
replaced with the recipient's CSV values (`{{ email }}` is always available).
Unknown placeholders are left untouched.

## Legacy scripts

`htmlEmail.py` and `singleEmailSernder.py` still work and now delegate to the
CLI using the same environment configuration:

```bash
python htmlEmail.py
python singleEmailSernder.py someone@example.com
```

## Tests

```bash
python -m pytest
```

The suite covers CSV parsing, templating, message construction, retry/failure
handling and the CLI, using a fake SMTP server — no mail is ever sent.

---

Author: Souvik Ghosh
