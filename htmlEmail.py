import smtplib, ssl
from smtplib import SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv


email="YOUR_EMAIL"
password= "PASSWORD_OF_YOUR_EMAIL"


with open("src/email.csv","r") as f:
    reader = csv.reader(f)
    recievers  = [row[0] for row in reader]

with open("src/msg.html","r", encoding="utf-8") as f:
    html = f.read()

with open("src/msg.txt","r", encoding="utf-8") as f:
    text = f.read()

for recipient in recievers:
    context = ssl.create_default_context()
    # if you are using gmail then smpt server address will be smtp.gmail.com
    # if you are using your webmail then smpt server address will be smtp.yourdomain.com or yourdomain.com
    with smtplib.SMTP_SSL("tronics.dev",465,context= context) as server:
        message = MIMEMultipart('alternative')
        message["Subject"] = "Test Subject"
        message["From"] = email
        message["To"] = recipient
        html_message = MIMEText(html, "html")
        text_message = MIMEText(text, "plain")
        print(text)

        message.attach(text_message)
        message.attach(html_message)

        server.login(email, password)
        server.sendmail(email, recipient, message.as_string())
        response_code , response_msg = server.noop()
        print(response_code, response_msg)
        server.quit()
