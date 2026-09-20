import smtplib

import pytest

from email_sender.config import SMTPConfig
from email_sender.recipients import Recipient
from email_sender.sender import EmailSender

CONFIG = SMTPConfig(
    host="smtp.example.com", username="me@example.com", password="secret", port=465
)


class FakeSMTP:
    instances: list["FakeSMTP"] = []

    def __init__(self, host, port, context=None, timeout=None):
        self.host = host
        self.port = port
        self.sent = []
        self.logged_in = None
        self.quit_called = False
        self.fail_for = set()
        FakeSMTP.instances.append(self)

    def login(self, username, password):
        self.logged_in = (username, password)

    def send_message(self, message):
        if message["To"] in self.fail_for:
            raise smtplib.SMTPRecipientsRefused({message["To"]: (550, b"nope")})
        self.sent.append(message)

    def quit(self):
        self.quit_called = True


@pytest.fixture
def fake_smtp(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    return FakeSMTP


def test_send_batch_reuses_one_connection(fake_smtp):
    recipients = [Recipient("a@example.com"), Recipient("b@example.com")]

    with EmailSender(CONFIG) as sender:
        results = sender.send_batch(recipients, "Hi", "text body", "<p>html</p>")

    assert [r.sent for r in results] == [True, True]
    assert len(fake_smtp.instances) == 1
    server = fake_smtp.instances[0]
    assert server.logged_in == ("me@example.com", "secret")
    assert [m["To"] for m in server.sent] == ["a@example.com", "b@example.com"]
    assert server.quit_called


def test_send_batch_continues_after_failure(fake_smtp):
    sender = EmailSender(CONFIG)
    sender.connect()
    fake_smtp.instances[0].fail_for = {"a@example.com"}

    results = sender.send_batch(
        [Recipient("a@example.com"), Recipient("b@example.com")], "Hi", "body"
    )
    sender.close()

    assert [(r.recipient, r.sent) for r in results] == [
        ("a@example.com", False),
        ("b@example.com", True),
    ]
    assert results[0].error


def test_dry_run_never_connects(fake_smtp):
    with EmailSender(CONFIG, dry_run=True) as sender:
        results = sender.send_batch([Recipient("a@example.com")], "Hi $email", "body $email")

    assert results == [type(results[0])(recipient="a@example.com", sent=True)]
    assert fake_smtp.instances == []


def test_dry_run_reports_template_errors(fake_smtp):
    with EmailSender(CONFIG, dry_run=True) as sender:
        results = sender.send_batch([Recipient("a@example.com")], "Hi", "Hello $name")

    assert results[0].sent is False
    assert "name" in results[0].error


def test_starttls_path(monkeypatch):
    created = {}

    class FakePlainSMTP(FakeSMTP):
        def starttls(self, context=None):
            created["starttls"] = True

    FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP", FakePlainSMTP)
    config = SMTPConfig(
        host="smtp.example.com",
        username="me@example.com",
        password="secret",
        port=587,
        use_ssl=False,
    )

    with EmailSender(config) as sender:
        sender.send_batch([Recipient("a@example.com")], "Hi", "body")

    assert created == {"starttls": True}
