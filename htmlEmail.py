import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from pathlib import Path
import re
import smtplib
import ssl

BASE_DIR = Path(__file__).resolve().parent
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

email = os.environ.get("SMTP_USER", "YOUR_EMAIL")
password = os.environ.get("SMTP_PASSWORD", "PASSWORD_OF_YOUR_EMAIL")
smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
smtp_port = int(os.environ.get("SMTP_PORT", "465"))

csv_file = BASE_DIR / "src" / "email.csv"
html_file = BASE_DIR / "src" / "msg.html"
text_file = BASE_DIR / "src" / "msg.txt"

# Read recipients
recipients = []
if csv_file.is_file():
    with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and EMAIL_PATTERN.fullmatch(row[0].strip()):
                recipients.append(row[0].strip())

# Read email bodies
html = html_file.read_text(encoding="utf-8", errors="ignore") if html_file.is_file() else ""
text = text_file.read_text(encoding="utf-8", errors="ignore") if text_file.is_file() else ""

if email == "YOUR_EMAIL" or password == "PASSWORD_OF_YOUR_EMAIL":
    print("Please set your credentials (or export SMTP_USER and SMTP_PASSWORD) before running.")
elif not recipients:
    print(f"No valid recipient emails found in {csv_file}")
else:
    context = ssl.create_default_context()
    print(f"Connecting to {smtp_host}:{smtp_port}...")
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(email, password)
        print(f"Authenticated successfully as {email}")

        for recipient in recipients:
            try:
                message = MIMEMultipart("alternative")
                message["Subject"] = "Thank You!"
                message["From"] = email
                message["To"] = recipient

                if text:
                    message.attach(MIMEText(text, "plain", "utf-8"))
                if html:
                    message.attach(MIMEText(html, "html", "utf-8"))

                server.sendmail(email, [recipient], message.as_string())
                print(f"[✓] Successfully sent to: {recipient}")
            except Exception as err:
                print(f"[✗] Failed to send to {recipient}: {err}")
