import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuration: Reads from environment variables if set, or uses placeholders below
email = os.environ.get("SMTP_USER", "YOUR_EMAIL")
password = os.environ.get("SMTP_PASSWORD", "PASSWORD_OF_YOUR_EMAIL")
smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
smtp_port = int(os.environ.get("SMTP_PORT", "465"))

recipient = os.environ.get("RECIPIENT", "shihabsikder98@gmail.com")

message = MIMEMultipart("alternative")
message["Subject"] = "Test Subject"
message["From"] = email
message["To"] = recipient
message.attach(MIMEText("This is a test email", "plain"))

context = ssl.create_default_context()

if email == "YOUR_EMAIL" or password == "PASSWORD_OF_YOUR_EMAIL":
    print("Please set your email and password (or export SMTP_USER and SMTP_PASSWORD) before running.")
else:
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(email, password)
        server.sendmail(email, recipient, message.as_string())
        response_code, response_msg = server.noop()
        print(f"Server response: {response_code} {response_msg}")
        print(f"Email successfully sent to {recipient}")
