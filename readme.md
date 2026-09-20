# Email Sender

Send templated plaintext + HTML emails over SMTP to one recipient or a CSV list,
from the command line.

## Install

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in your SMTP credentials
```

Credentials are read from the environment (or `.env`), never hard-coded:

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `SMTP_HOST` | yes | – | e.g. `smtp.gmail.com` |
| `SMTP_USERNAME` | yes | – | login / default From address |
| `SMTP_PASSWORD` | yes | – | Gmail needs an app password |
| `SMTP_PORT` | no | 465 (SSL) / 587 (STARTTLS) | |
| `SMTP_USE_SSL` | no | `true` | set `false` for STARTTLS |
| `SMTP_SENDER` | no | `SMTP_USERNAME` | From override |
| `SMTP_SENDER_NAME` | no | – | display name |

## Usage

```bash
# Validate recipients and templates without sending anything
python -m email_sender.cli --csv src/email.csv --dry-run

# Send the HTML + plaintext templates to everyone in the CSV
python -m email_sender.cli --csv src/email.csv --subject "Thank you, $name"

# One-off message, no CSV
python -m email_sender.cli --to someone@example.com --subject "Hi" --text src/msg.txt
```

Options: `--csv`, `--to` (repeatable), `--subject`, `--html`, `--text`,
`--attach` (repeatable), `--env-file`, `--delay`, `--dry-run`, `--verbose`.
Exit code is `0` on success, `1` if any message failed, `2` for bad
configuration or input.

## Templates and recipients

`src/email.csv` may be a bare column of addresses, or have a header row with an
`email` column; every other column becomes a template variable for that row.

```csv
name,email
Ada,ada@example.com
```

Subject and body files substitute `$name` / `${name}` placeholders, plus
`$email` which is always available. Invalid and duplicate addresses are skipped;
a failed send is reported and the run continues with the next recipient.

## Tests

```bash
python -m pytest
```

Author: Souvik Ghosh
