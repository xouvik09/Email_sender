# Dispatch — Professional SMTP Email Delivery Engine

A production-ready, zero-dependency email delivery system and bulk dispatch platform built on the **Python standard library** (`http.server`, `smtplib`, `ssl`, `email.mime.*`) and modern vanilla JavaScript.

Designed for real-world deployment on **Vercel**, Linux VPS, or cloud containers with high reliability, clean UX, and strict RFC-compliant MIME formatting.

---

## Deploy to Vercel (1-Click or CLI)

This project is pre-configured with `vercel.json` and serverless Python handlers in `api/index.py`.

### Option A: Deploy via GitHub (Recommended)
1. Push your repository to GitHub (already linked: `https://github.com/xouvik09/Email_sender`).
2. Go to **[vercel.com](https://vercel.com/)** and log in.
3. Click **"Add New..."** &rarr; **"Project"**.
4. Import your **`Email_sender`** repository.
5. Click **Deploy**. Vercel will automatically build the static assets and serverless Python API.

*(Optional)* In the Vercel Project Settings &rarr; **Environment Variables**, you can define `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM` if you want default credentials pre-loaded.

### Option B: Deploy via Vercel CLI
```bash
# Install Vercel CLI if you haven't already
npm i -g vercel

# Run deploy from the project folder
vercel
```

---

## Key Features

- **Real SMTP Delivery**: Direct authenticated delivery over SSL/TLS (port 465) or STARTTLS (port 587).
- **Dual Format Support**:
  - **Normal Mail (Plain Text)**: Standard plain-text formatting, clean typography, character & word counters, greeting/sign-off insertion.
  - **Rich HTML Mail**: Code editor with inline HTML formatting controls (`<p>`, `<b>`, `<h2>`, CTA buttons, card containers) and plain-text fallback generation.
- **Provider Presets**: Instant 1-click configuration for **Gmail**, **Microsoft 365 / Outlook**, **Yahoo Mail**, or **Custom SMTP**.
- **Attachment Support**: Native base64 MIME multipart encoding for documents, PDFs, images, and spreadsheets up to 25MB.
- **Recipient Import & Batching**: Direct input or one-click CSV / text import with real-time address validation.
- **Pre-flight Connection Tester**: Authenticate your credentials with your SMTP host prior to dispatch.
- **Live Email Client Preview**: Real-time rendering of email headers (`From`, `To`, `Subject`, `Format`) and message body.
- **Transmission Audit Log**: Session log recording delivery status, timestamps, recipient count, and mail format.
- **Zero Third-Party Dependencies**: No `requests`, no `flask`, no `django`, no `npm` required. Uses purely Python's standard library.

---

## Quick Start (Run Locally)

### 1. Run the Server
```bash
python app.py
```

### 2. Access the Console
Open your browser at:
```
http://127.0.0.1:8000
```

---

## Mail Provider Setup

### Gmail
1. Select the **Gmail** provider button (sets host `smtp.gmail.com`, port `465`, SSL).
2. In **Username**, enter your full Gmail address.
3. In **Password**, enter a **16-character Google App Password**:
   - Go to [Google Account Security](https://myaccount.google.com/security).
   - Ensure **2-Step Verification** is enabled.
   - Go to [App Passwords](https://myaccount.google.com/apppasswords).
   - Generate an app password for `Dispatch` and paste the 16 characters into the password field.

### Microsoft 365 / Outlook
1. Select the **Outlook / 365** provider button (sets host `smtp.office365.com`, port `587`, STARTTLS).
2. Enter your Microsoft 365 or Outlook email and account/app password.

### Yahoo Mail
1. Select the **Yahoo** provider button (sets host `smtp.mail.yahoo.com`, port `465`, SSL).
2. Generate an App Password in Yahoo Account Security settings and paste into the password field.

### Custom SMTP Server
Select **Custom** and enter your corporate or hosting provider's SMTP host, port, credentials, and SSL or STARTTLS encryption mode.

---

## Environment Configuration (`.env`)

For local development or persistent credentials without manual browser input, create a `.env` file in the project directory:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com
SMTP_SECURITY=ssl
APP_HOST=0.0.0.0
APP_PORT=8000
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System status and active server SMTP configuration |
| `GET` | `/api/templates` | Ready-to-use email templates (HTML & Plain Text) |
| `GET` | `/api/history` | Audit log of sent email transmissions |
| `POST` | `/api/verify` | Tests SMTP host connectivity and authentication |
| `POST` | `/api/send` | Executes real email dispatch via authenticated SMTP |
