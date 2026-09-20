import csv
import io
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.datastructures import FileStorage

from email_sender.config import ConfigError, SMTPConfig
from email_sender.message import TemplateError, render
from email_sender.recipients import (
    Recipient,
    RecipientError,
    is_valid_email,
    parse_recipients,
)
from email_sender.sender import EmailSender

DEFAULT_TEXT = Path("src/msg.txt")
DEFAULT_HTML = Path("src/msg.html")
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


class RequestError(Exception):
    """Raised when the submitted form cannot be turned into a send job."""


def create_app(dry_run_only: bool = False) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    app.config["DRY_RUN_ONLY"] = dry_run_only

    @app.get("/")
    def index() -> str:
        return render_template(
            "index.html",
            default_text=_read_default(DEFAULT_TEXT),
            default_html=_read_default(DEFAULT_HTML),
            dry_run_only=app.config["DRY_RUN_ONLY"],
        )

    @app.get("/api/config")
    def config_status():
        try:
            config = SMTPConfig.from_env()
        except ConfigError as exc:
            return jsonify({"configured": False, "detail": str(exc)})
        return jsonify(
            {
                "configured": True,
                "host": config.host,
                "port": config.port,
                "use_ssl": config.use_ssl,
                "from": config.from_address,
            }
        )

    @app.post("/api/preview")
    def preview():
        try:
            job = _parse_request()
        except (RequestError, RecipientError) as exc:
            return jsonify({"error": str(exc)}), 400

        first = job["recipients"][0]
        try:
            rendered = {
                "subject": render(job["subject"], first.context),
                "text": render(job["text"], first.context),
                "html": render(job["html"], first.context) if job["html"] else "",
            }
        except TemplateError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify(
            {
                "recipients": [r.email for r in job["recipients"]],
                "preview_for": first.email,
                **rendered,
            }
        )

    @app.post("/api/send")
    def send():
        try:
            job = _parse_request()
        except (RequestError, RecipientError) as exc:
            return jsonify({"error": str(exc)}), 400

        dry_run = job["dry_run"] or app.config["DRY_RUN_ONLY"]
        if dry_run:
            config = SMTPConfig(host="dry-run", username="dry-run@example.com", password="")
        else:
            try:
                config = SMTPConfig.from_env()
            except ConfigError as exc:
                return jsonify({"error": str(exc)}), 400

        try:
            with EmailSender(config, dry_run=dry_run) as sender:
                results = sender.send_batch(
                    recipients=job["recipients"],
                    subject=job["subject"],
                    text_body=job["text"],
                    html_body=job["html"] or None,
                )
        except OSError as exc:
            return jsonify({"error": f"SMTP connection failed: {exc}"}), 502

        return jsonify(
            {
                "dry_run": dry_run,
                "sent": sum(1 for result in results if result.sent),
                "total": len(results),
                "results": [
                    {"recipient": r.recipient, "sent": r.sent, "error": r.error} for r in results
                ],
            }
        )

    return app


def _read_default(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _parse_request() -> dict:
    form = request.form
    subject = (form.get("subject") or "").strip()
    text = form.get("text") or ""
    html = form.get("html") or ""

    if not subject:
        raise RequestError("Subject is required.")
    if not text.strip():
        raise RequestError("A plaintext body is required.")

    recipients = _parse_recipients(form.get("recipients") or "", request.files.get("csv"))
    if not recipients:
        raise RequestError("Add at least one valid recipient.")

    return {
        "subject": subject,
        "text": text,
        "html": html,
        "recipients": recipients,
        "dry_run": form.get("dry_run") in {"1", "true", "on"},
    }


def _parse_recipients(raw: str, upload: FileStorage | None) -> list[Recipient]:
    recipients: list[Recipient] = []
    seen: set[str] = set()

    def add(recipient: Recipient) -> None:
        key = recipient.email.lower()
        if key not in seen:
            seen.add(key)
            recipients.append(recipient)

    for chunk in raw.replace(";", ",").replace("\n", ",").split(","):
        address = chunk.strip()
        if not address:
            continue
        if not is_valid_email(address):
            raise RequestError(f"Not a valid email address: {address}")
        add(Recipient(email=address))

    if upload and upload.filename:
        for recipient in _recipients_from_upload(upload):
            add(recipient)

    return recipients


def _recipients_from_upload(upload: FileStorage) -> list[Recipient]:
    content = upload.read().decode("utf-8-sig", errors="replace")
    name = Path(upload.filename or "upload.csv").name
    return parse_recipients(csv.reader(io.StringIO(content)), source=name)
