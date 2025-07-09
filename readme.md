# Installation
install the requirements files

# Email Sending Script

This is a simple Python script to send emails with custom templates of personal choise in HTML formate using SMTP.

## Usage

Update the following variables in the script:

- `email` - The email address to send from
- `password` - The password for the email address
- `recipient` - The recipient's email address
- `SMTP_SERVER_ADDRESS` - The SMTP server address. For Gmail this is `smtp.gmail.com`

Run the script:

```
python singleEmailSernder.py
```

An email will be sent to the recipient address with the subject "Test Subject" and plain text body "This is a test email".

## Libraries Used

- smtplib - Used for connecting to the SMTP server and sending the email
- SSL - Used for creating a SSL context to connect securely
- MIMEMultipart - Used for constructing the email message with text and attachments
- MIMEText - Used for the text body of the email message

## How it Works

- Connects to the SMTP server using SSL
- Logs in with the provided username and password
- Constructs the email message with recipient, subject, and plaintext body
- Sends the message
- Prints the response code and message from the server
- Closes the connection

So in summary, this script provides a simple way to send automated emails using Python by connecting to an SMTP server.

# Email Sending Script with HTML

This Python script sends emails with HTML formatting using SMTP.

## Usage

Update the following variables:

- `email` - The sender email address
- `password` - The password for the sender email
- `receivers` - List of recipient email addresses in email.csv
- `html` - HTML email body in msg.html
- `text` - Plaintext email body in msg.txt

Run the script:

```
pip install requirements.txt
python htmlEmail.py
```

It will send an email to each recipient with the HTML and plaintext bodies.

## How it works

- Opens email.csv containing list of recipient emails
- Reads in HTML email body from msg.html
- Reads in plaintext body from msg.txt
- Loops through each recipient
  - Constructs MIME multipart message with HTML and plaintext
  - Sets subject, from, and to fields
  - Logs into SMTP server
  - Sends message
  - Prints response from server
- Closes SMTP connection when done

So in summary, this script sends emails with HTML formatting to multiple recipients using CSV and SMTP.

## Libraries used

- smtplib
- SSL
- MIMEMultipart
- MIMEText
- csv

Let me know if you need any other clarification!


Author: Souvik Ghosh
Email: Souvik.ghosh.9279@gmail.com