import pytest

from email_sender.config import ConfigError, SMTPConfig

REQUIRED = {
    "SMTP_HOST": "smtp.example.com",
    "SMTP_USERNAME": "me@example.com",
    "SMTP_PASSWORD": "secret",
}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in (
        "SMTP_HOST",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_PORT",
        "SMTP_USE_SSL",
        "SMTP_SENDER",
        "SMTP_SENDER_NAME",
    ):
        monkeypatch.delenv(name, raising=False)


def test_from_env_defaults_to_ssl_port(monkeypatch):
    for key, value in REQUIRED.items():
        monkeypatch.setenv(key, value)

    config = SMTPConfig.from_env(env_file="/nonexistent.env")

    assert (config.host, config.port, config.use_ssl) == ("smtp.example.com", 465, True)
    assert config.from_address == "me@example.com"


def test_from_env_uses_starttls_port_when_ssl_disabled(monkeypatch):
    for key, value in REQUIRED.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("SMTP_USE_SSL", "false")

    config = SMTPConfig.from_env(env_file="/nonexistent.env")

    assert (config.port, config.use_ssl) == (587, False)


def test_from_env_formats_display_name(monkeypatch):
    for key, value in REQUIRED.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("SMTP_SENDER", "noreply@example.com")
    monkeypatch.setenv("SMTP_SENDER_NAME", "Tronics")

    assert SMTPConfig.from_env(env_file="/nonexistent.env").from_address == (
        "Tronics <noreply@example.com>"
    )


def test_from_env_reports_missing_variables(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")

    with pytest.raises(ConfigError, match="SMTP_USERNAME"):
        SMTPConfig.from_env(env_file="/nonexistent.env")


def test_from_env_rejects_non_integer_port(monkeypatch):
    for key, value in REQUIRED.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("SMTP_PORT", "abc")

    with pytest.raises(ConfigError, match="SMTP_PORT"):
        SMTPConfig.from_env(env_file="/nonexistent.env")
