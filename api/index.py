"""Dispatch Email Server & Vercel Serverless Function."""
import base64
import email.encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import smtplib
import ssl
import time
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Load .env if present locally
DOTENV_PATH = BASE_DIR / ".env"
if DOTENV_PATH.is_file():
    try:
        for line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k and k not in os.environ:
                os.environ[k] = v
    except Exception:
        pass

# In-memory session audit history
TRANSMISSION_HISTORY = []
MAX_HISTORY = 100


def json_response(handler_inst, status, payload):
    body = json.dumps(payload, default=str).encode("utf-8")
    handler_inst.send_response(status)
    handler_inst.send_header("Content-Type", "application/json; charset=utf-8")
    handler_inst.send_header("Content-Length", str(len(body)))
    handler_inst.send_header("Access-Control-Allow-Origin", "*")
    handler_inst.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler_inst.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler_inst.end_headers()
    handler_inst.wfile.write(body)


def read_json(handler_inst):
    content_length = int(handler_inst.headers.get("Content-Length", "0"))
    if content_length > 25_000_000:
        raise ValueError("Payload size exceeds 25MB attachment limit")
    raw = handler_inst.rfile.read(content_length)
    return json.loads(raw.decode("utf-8") if raw else "{}")


def strip_html_tags(html_content):
    if not html_content:
        return ""
    clean = re.compile(r"<[^>]+>")
    text = clean.sub("", html_content)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def format_smtp_error(err):
    err_str = str(err)
    if isinstance(err, smtplib.SMTPAuthenticationError) or "535" in err_str or "Username and Password not accepted" in err_str:
        return "Authentication Failed (535): Incorrect username or password. If using Gmail, Yahoo, or Outlook, you must use a dedicated App Password instead of your regular login password."
    if "getaddrinfo failed" in err_str or "Name or service not known" in err_str:
        return "Could not resolve SMTP server hostname. Please verify your host address."
    if "timed out" in err_str or "TimeoutError" in err_str:
        return "Connection timed out. Check the SMTP host, port, and security settings (SSL vs STARTTLS)."
    if isinstance(err, smtplib.SMTPSenderRefused) or "Sender address rejected" in err_str:
        return f"Sender address rejected by mail server: {err_str}"
    if isinstance(err, smtplib.SMTPRecipientsRefused):
        return f"Recipient address rejected by mail server: {err_str}"
    return f"SMTP Delivery Error: {err_str}"


def get_default_smtp():
    return {
        "host": os.environ.get("SMTP_HOST", "").strip(),
        "port": int(os.environ.get("SMTP_PORT", "465")),
        "username": os.environ.get("SMTP_USER", "") or os.environ.get("SMTP_USERNAME", "").strip(),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "sender": os.environ.get("SMTP_FROM", "") or os.environ.get("SMTP_SENDER", "") or os.environ.get("SMTP_USER", "").strip(),
        "security": os.environ.get("SMTP_SECURITY", "ssl").lower(),
    }


def verify_smtp_connection(smtp_settings):
    smtp_host = smtp_settings["host"]
    smtp_port = smtp_settings["port"]
    smtp_user = smtp_settings["username"]
    smtp_password = smtp_settings["password"]
    security = smtp_settings.get("security", "ssl")

    if not all((smtp_host, smtp_user, smtp_password)):
        raise ValueError("SMTP host, username, and password are required to test connection")

    context = ssl.create_default_context()
    if security == "starttls":
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        try:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(smtp_user, smtp_password)
        finally:
            try:
                server.quit()
            except Exception:
                pass
    else:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=15)
        try:
            server.login(smtp_user, smtp_password)
        finally:
            try:
                server.quit()
            except Exception:
                pass
    return True


def attach_file_part(root_message, attachment):
    filename = attachment.get("filename", "attachment")
    b64_data = attachment.get("content", "")
    mime_type = attachment.get("type") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    maintype, subtype = mime_type.split("/", 1) if "/" in mime_type else ("application", "octet-stream")

    part = MIMEBase(maintype, subtype)
    part.set_payload(base64.b64decode(b64_data))
    email.encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    root_message.attach(part)


def build_email_message(sender, recipient, subject, text_body, html_body, attachments=None, mail_format="text"):
    attachments = attachments or []

    if mail_format == "text":
        if attachments:
            root_message = MIMEMultipart("mixed")
            root_message["Subject"] = subject
            root_message["From"] = sender
            root_message["To"] = recipient
            root_message.attach(MIMEText(text_body, "plain", "utf-8"))
            for att in attachments:
                attach_file_part(root_message, att)
            return root_message
        else:
            msg = MIMEText(text_body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipient
            return msg
    else:
        plain_fallback = text_body if text_body else strip_html_tags(html_body)
        if not plain_fallback:
            plain_fallback = "This email requires an HTML-capable email viewer."

        if attachments:
            root_message = MIMEMultipart("mixed")
            root_message["Subject"] = subject
            root_message["From"] = sender
            root_message["To"] = recipient

            body_container = MIMEMultipart("alternative")
            body_container.attach(MIMEText(plain_fallback, "plain", "utf-8"))
            body_container.attach(MIMEText(html_body, "html", "utf-8"))
            root_message.attach(body_container)

            for att in attachments:
                attach_file_part(root_message, att)
            return root_message
        else:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender
            message["To"] = recipient
            message.attach(MIMEText(plain_fallback, "plain", "utf-8"))
            message.attach(MIMEText(html_body, "html", "utf-8"))
            return message


def execute_smtp_delivery(recipients, subject, text_body, html_body, smtp_settings, attachments=None, mail_format="text"):
    sender = smtp_settings["sender"]
    smtp_host = smtp_settings["host"]
    smtp_port = smtp_settings["port"]
    smtp_user = smtp_settings["username"]
    smtp_password = smtp_settings["password"]
    security = smtp_settings.get("security", "ssl")
    attachments = attachments or []

    if not all((smtp_host, smtp_user, smtp_password, sender)):
        raise ValueError("All SMTP fields (Host, Port, Username, Password, From Address) are required for delivery.")

    context = ssl.create_default_context()
    if security == "starttls":
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
    else:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=30)

    sent_count = 0
    failed_count = 0
    results = []
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    with server:
        server.login(smtp_user, smtp_password)
        for recipient in recipients:
            try:
                msg = build_email_message(sender, recipient, subject, text_body, html_body, attachments, mail_format)
                server.sendmail(sender, [recipient], msg.as_string())
                sent_count += 1
                results.append({"recipient": recipient, "status": "delivered"})
            except Exception as exc:
                failed_count += 1
                results.append({"recipient": recipient, "status": "failed", "error": format_smtp_error(exc)})

    summary = {
        "timestamp": timestamp,
        "subject": subject,
        "sender": sender,
        "recipients_count": len(recipients),
        "sent_count": sent_count,
        "failed_count": failed_count,
        "mail_format": mail_format,
        "results": results,
        "attachments": [a.get("filename") for a in attachments],
    }
    TRANSMISSION_HISTORY.insert(0, summary)
    if len(TRANSMISSION_HISTORY) > MAX_HISTORY:
        TRANSMISSION_HISTORY.pop()
    return summary


class handler(BaseHTTPRequestHandler):
    """Vercel and local BaseHTTPRequestHandler."""

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/api/health", "/health"):
            defaults = get_default_smtp()
            has_server_config = bool(defaults["host"] and defaults["username"])
            json_response(self, HTTPStatus.OK, {
                "status": "online",
                "smtp_configured": has_server_config,
                "default_smtp": {
                    "host": defaults["host"],
                    "port": defaults["port"],
                    "sender": defaults["sender"],
                    "security": defaults["security"],
                }
            })
            return

        if path in ("/api/templates", "/templates"):
            templates = [
                {
                    "id": "business_announcement",
                    "name": "Product Announcement (HTML)",
                    "format": "html",
                    "subject": "Important Product Update & New Features",
                    "html": """<div style="max-width: 600px; margin: auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
    <div style="background: #14201e; padding: 32px 24px; text-align: center; color: #ffffff;">
        <h1 style="margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">Product Update</h1>
        <p style="margin: 8px 0 0; font-size: 14px; color: #d4ee5b;">Discover our latest capabilities</p>
    </div>
    <div style="padding: 32px 28px; color: #334155; line-height: 1.65; font-size: 15px;">
        <p>Hello,</p>
        <p>We are excited to announce new platform enhancements designed to make your email operations faster and more reliable.</p>
        <div style="margin: 24px 0; padding: 18px 20px; background: #f8fafc; border-left: 4px solid #d4ee5b; border-radius: 4px;">
            <strong style="color: #14201e;">What is new:</strong>
            <ul style="margin: 8px 0 0; padding-left: 20px; color: #475569;">
                <li>Direct authenticated SMTP transmission</li>
                <li>Support for both Plain Text and Rich HTML</li>
                <li>Instant recipient rendering and attachment support</li>
            </ul>
        </div>
        <p style="font-size: 13px; color: #64748b; margin-top: 24px; border-top: 1px solid #f1f5f9; padding-top: 16px;">
            Have questions? Simply reply directly to this email.
        </p>
    </div>
</div>""",
                    "text": "Hello,\n\nWe are excited to announce new platform enhancements designed to make your email operations faster and more reliable.\n\nWhat is new:\n- Direct authenticated SMTP transmission\n- Support for both Plain Text and Rich HTML\n- Instant recipient rendering and attachment support\n\nBest regards,\nThe Team",
                },
                {
                    "id": "meeting_followup",
                    "name": "Meeting Follow-Up (Plain Text)",
                    "format": "text",
                    "subject": "Follow-Up: Summary of Action Items",
                    "html": "",
                    "text": "Hi team,\n\nThank you for taking the time to meet today. Here is a brief recap of our discussion and agreed next steps:\n\n1. Finalize the deployment environment\n2. Verify production SMTP credentials\n3. Deliver initial batch and review logs\n\nPlease let me know if you have any feedback or if anything needs adjustment.\n\nBest regards,\nYour Name",
                }
            ]
            json_response(self, HTTPStatus.OK, {"templates": templates})
            return

        if path in ("/api/history", "/history"):
            json_response(self, HTTPStatus.OK, {"history": TRANSMISSION_HISTORY})
            return

        # Fallback for local static file serving when running locally
        if path in ("/", "/index.html"):
            self.serve_file(FRONTEND_DIR / "index.html", "text/html; charset=utf-8")
            return

        if path.startswith("/assets/"):
            filename = Path(path.removeprefix("/assets/")).name
            asset_path = FRONTEND_DIR / "assets" / filename
            content_type = {
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon",
                ".png": "image/png",
            }.get(asset_path.suffix, "application/octet-stream")
            self.serve_file(asset_path, content_type)
            return

        json_response(self, HTTPStatus.NOT_FOUND, {"error": "Endpoint not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/api/verify", "/verify"):
            try:
                payload = read_json(self)
                smtp = payload.get("smtp", {})
                defaults = get_default_smtp()
                smtp_settings = {
                    "host": str(smtp.get("host") or defaults["host"]).strip(),
                    "port": int(smtp.get("port") or defaults["port"]),
                    "username": str(smtp.get("username") or defaults["username"]).strip(),
                    "password": str(smtp.get("password") or defaults["password"]),
                    "security": str(smtp.get("security") or defaults["security"]).lower(),
                }
                verify_smtp_connection(smtp_settings)
                json_response(self, HTTPStatus.OK, {"status": "ok", "message": "SMTP connection & authentication successful. Ready to send."})
            except ValueError as err:
                json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(err)})
            except (OSError, smtplib.SMTPException) as err:
                json_response(self, HTTPStatus.BAD_GATEWAY, {"error": format_smtp_error(err)})
            except Exception as err:
                json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(err)})
            return

        if path in ("/api/send", "/send"):
            try:
                payload = read_json(self)
                recipients = payload.get("recipients", [])
                if isinstance(recipients, str):
                    recipients = recipients.replace(",", "\n").splitlines()
                recipients = list(dict.fromkeys(item.strip() for item in recipients if item.strip()))

                subject = str(payload.get("subject", "")).strip()
                text_body = str(payload.get("text", "")).strip()
                html_body = str(payload.get("html", "")).strip()
                mail_format = str(payload.get("format", "text")).lower()
                if mail_format not in ("text", "html"):
                    mail_format = "html" if html_body else "text"

                attachments = payload.get("attachments", [])
                smtp = payload.get("smtp", {})
                defaults = get_default_smtp()

                security = str(smtp.get("security") or defaults["security"]).lower()
                try:
                    port_val = smtp.get("port") or defaults["port"]
                    smtp_port = int(port_val)
                except (TypeError, ValueError):
                    raise ValueError("SMTP port must be a valid integer")

                smtp_settings = {
                    "host": str(smtp.get("host") or defaults["host"]).strip(),
                    "port": smtp_port,
                    "username": str(smtp.get("username") or defaults["username"]).strip(),
                    "password": str(smtp.get("password") or defaults["password"]),
                    "sender": str(smtp.get("sender") or defaults["sender"]).strip(),
                    "security": security,
                }

                if not recipients:
                    raise ValueError("Please provide at least one recipient email address")
                if len(recipients) > 500:
                    raise ValueError("Recipient limit is 500 per dispatch batch")

                invalid_recipients = [item for item in recipients if not EMAIL_PATTERN.fullmatch(item)]
                if invalid_recipients:
                    raise ValueError(f"Invalid email address: {invalid_recipients[0]}")

                if not subject:
                    raise ValueError("Subject line is required")

                if mail_format == "text" and not text_body:
                    raise ValueError("Message body cannot be empty")
                if mail_format == "html" and not html_body and not text_body:
                    raise ValueError("HTML content cannot be empty")

                # Validate SMTP fields
                missing = []
                if not smtp_settings["host"]: missing.append("SMTP Host")
                if not smtp_settings["username"]: missing.append("Username / Email")
                if not smtp_settings["password"]: missing.append("Password / App Password")
                if not smtp_settings["sender"]: missing.append("From Address")
                if missing:
                    raise ValueError(f"Missing required SMTP configuration: {', '.join(missing)}")
                if not 1 <= smtp_port <= 65535:
                    raise ValueError("SMTP port must be between 1 and 65535")
                if security not in ("ssl", "starttls"):
                    raise ValueError("SMTP security must be SSL or STARTTLS")

                summary = execute_smtp_delivery(recipients, subject, text_body, html_body, smtp_settings, attachments, mail_format)
                fmt_label = "Plain Text" if mail_format == "text" else "HTML"
                
                if summary["failed_count"] == 0:
                    msg_text = f"Delivered {fmt_label} email to {summary['sent_count']} recipient{'s' if summary['sent_count'] > 1 else ''} successfully."
                elif summary["sent_count"] > 0:
                    msg_text = f"Partially delivered: {summary['sent_count']} sent, {summary['failed_count']} failed."
                else:
                    first_err = summary["results"][0].get("error", "Delivery failed")
                    raise smtplib.SMTPException(first_err)

                json_response(self, HTTPStatus.OK, {
                    "message": msg_text,
                    "summary": summary
                })
            except ValueError as error:
                json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(error)})
            except (OSError, smtplib.SMTPException, RuntimeError) as error:
                json_response(self, HTTPStatus.BAD_GATEWAY, {"error": format_smtp_error(error)})
            except Exception as error:
                json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Internal server error: {str(error)}"})
            return

        json_response(self, HTTPStatus.NOT_FOUND, {"error": "Endpoint not found"})

    def serve_file(self, path, content_type):
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            json_response(self, HTTPStatus.NOT_FOUND, {"error": "File not found"})
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string, *args):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {self.address_string()} - {format_string % args}")


# Vercel exports
app = handler
application = handler


def run_local_server():
    host = os.environ.get("APP_HOST", "0.0.0.0") if os.environ.get("APP_HOST") else "127.0.0.1"
    port = int(os.environ.get("APP_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), handler)
    print("=========================================================")
    print(" Dispatch Production Mail Server")
    print(f" Running at http://{host}:{port}")
    print(" Ready for authenticated SMTP deliveries")
    print("=========================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.server_close()
