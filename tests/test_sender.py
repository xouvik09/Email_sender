import smtplib

import pytest

from email_sender import sender
from email_sender.config import ConfigError, SmtpConfig
from email_sender.message import Recipient


class FakeServer:
    def __init__(self, fail_times=0):
        self.fail_times = fail_times
        self.sent = []
        self.quit_called = False

    def send_message(self, message, from_addr, to_addrs):
        if self.fail_times > 0:
            self.fail_times -= 1
            raise smtplib.SMTPException("temporary failure")
        self.sent.append((from_addr, to_addrs, message["Subject"]))

    def quit(self):
        self.quit_called = True


@pytest.fixture
def config():
    return SmtpConfig(
        host="smtp.example.com",
        username="me@example.com",
        password="secret",
        sender_name="Me",
    )


@pytest.fixture
def patched_connection(monkeypatch):
    servers = []

    def factory(fail_times=0):
        server = FakeServer(fail_times)
        servers.append(server)

        class Connection:
            def __enter__(self):
                return server

            def __exit__(self, *exc):
                server.quit()
                return False

        monkeypatch.setattr(sender, "open_connection", lambda config: Connection())
        return server

    return factory


def test_send_bulk_sends_each_recipient(config, patched_connection):
    server = patched_connection()
    results = sender.send_bulk(
        config,
        [Recipient("a@example.com", {"name": "Ann"}), Recipient("b@example.com")],
        subject="Hi {{ name }}",
        text="Hello {{ name }}",
    )
    assert all(result.sent for result in results)
    assert [entry[1] for entry in server.sent] == [["a@example.com"], ["b@example.com"]]
    assert server.sent[0][0] == "me@example.com"
    assert server.sent[0][2] == "Hi Ann"
    assert server.quit_called


def test_send_bulk_retries_then_succeeds(config, patched_connection):
    server = patched_connection(fail_times=1)
    results = sender.send_bulk(
        config, [Recipient("a@example.com")], subject="Hi", text="Hello", retries=2
    )
    assert results[0].sent
    assert len(server.sent) == 1


def test_send_bulk_reports_failure(config, patched_connection):
    patched_connection(fail_times=5)
    results = sender.send_bulk(
        config, [Recipient("a@example.com")], subject="Hi", text="Hello", retries=2
    )
    assert not results[0].sent
    assert "temporary failure" in results[0].error


def test_dry_run_does_not_connect(config, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("should not connect during dry run")

    monkeypatch.setattr(sender, "open_connection", fail)
    results = sender.send_bulk(
        config, [Recipient("a@example.com")], subject="Hi", text="Hello", dry_run=True
    )
    assert results[0].sent


def test_from_address_includes_display_name(config):
    assert config.from_address == "Me <me@example.com>"
    assert config.envelope_from == "me@example.com"


def test_config_from_env_requires_credentials():
    with pytest.raises(ConfigError):
        SmtpConfig.from_env({"SMTP_HOST": "smtp.example.com"})


def test_config_from_env_defaults_starttls_port():
    config = SmtpConfig.from_env(
        {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_USERNAME": "me@example.com",
            "SMTP_PASSWORD": "secret",
            "SMTP_USE_SSL": "false",
        }
    )
    assert (config.port, config.use_ssl) == (587, False)
