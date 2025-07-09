import smtplib, ssl
from smtplib import SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

email="YOUR_EMAIL"
password= "PASSWORD_OF_YOUR_EMAIL"

recipient = "shihabsikder98@gmail.com"

message = MIMEMultipart('alternative')
message["Subject"] = "Test Subject"
message["From"] = email
message["To"] = recipient
message.attach(MIMEText("This is a test email", "plain"))

context = ssl.create_default_context()
# if you are using gmail then smpt server address will be smtp.gmail.com
# if you are using your webmail then smpt server address will be smtp.yourdomain.com or yourdomain.com

with smtplib.SMTP_SSL("SMTP_SERVER_ADDRESS", 465,context= context) as server:
    server.login(email, password)
    server.sendmail(email, recipient, message.as_string())
    response_code , response_msg = server.noop()
    print(response_code, response_msg)
    server.quit()
