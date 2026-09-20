import io
import smtplib

import pytest

from email_sender.web import create_app
from tests.test_sender import FakeSMTP


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


BASE_FORM = {
    "subject": "Hello $name",
    "text": "Hi $name",
    "html": "<p>Hi $name</p>",
    "recipients": "ada@example.com",
    "dry_run": "1",
}


def test_index_renders_compose_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'id="compose"' in response.data


def test_preview_renders_first_recipient(client):
    response = client.post(
        "/api/preview",
        data=dict(
            BASE_FORM,
            recipients="a@x.com; b@x.com",
            subject="Hello $email",
            text="Hi $email",
            html="<p>Hi $email</p>",
        ),
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["recipients"] == ["a@x.com", "b@x.com"]
    assert payload["preview_for"] == "a@x.com"
    assert payload["subject"] == "Hello a@x.com"
    assert payload["html"] == "<p>Hi a@x.com</p>"


def test_preview_reports_missing_template_variable(client):
    response = client.post("/api/preview", data=BASE_FORM)

    assert response.status_code == 400
    assert "name" in response.get_json()["error"]


def test_preview_uses_csv_columns(client):
    data = dict(BASE_FORM, recipients="")
    data["csv"] = (io.BytesIO(b"name,email\nAda,ada@example.com\n"), "list.csv")

    payload = client.post(
        "/api/preview", data=data, content_type="multipart/form-data"
    ).get_json()

    assert payload["subject"] == "Hello Ada"
    assert payload["html"] == "<p>Hi Ada</p>"


def test_invalid_recipient_is_rejected(client):
    response = client.post("/api/preview", data=dict(BASE_FORM, recipients="nope"))

    assert response.status_code == 400
    assert "nope" in response.get_json()["error"]


def test_missing_subject_is_rejected(client):
    response = client.post("/api/send", data=dict(BASE_FORM, subject=" "))

    assert response.status_code == 400
    assert "Subject" in response.get_json()["error"]


def test_dry_run_send_does_not_connect(client, monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    payload = client.post(
        "/api/send", data=dict(BASE_FORM, subject="Hi", text="Hi $email", html="")
    ).get_json()

    assert payload == {
        "dry_run": True,
        "sent": 1,
        "total": 1,
        "results": [{"recipient": "ada@example.com", "sent": True, "error": ""}],
    }
    assert FakeSMTP.instances == []


def test_real_send_uses_configured_smtp(client, monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "me@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")

    data = dict(BASE_FORM, subject="Hi", text="Hi $email", html="", recipients="ada@example.com")
    data.pop("dry_run")

    payload = client.post("/api/send", data=data).get_json()

    assert payload["dry_run"] is False
    assert payload["sent"] == 1
    assert [m["To"] for m in FakeSMTP.instances[0].sent] == ["ada@example.com"]


def test_send_without_credentials_reports_error(client, monkeypatch):
    for name in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    data = dict(BASE_FORM, subject="Hi", text="Hi $email")
    data.pop("dry_run")

    response = client.post("/api/send", data=data)

    assert response.status_code == 400
    assert "SMTP_HOST" in response.get_json()["error"]


def test_dry_run_only_app_forces_dry_run(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "me@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    client = create_app(dry_run_only=True).test_client()

    data = dict(BASE_FORM, subject="Hi", text="Hi $email", html="")
    data.pop("dry_run")

    payload = client.post("/api/send", data=data).get_json()

    assert payload["dry_run"] is True
    assert FakeSMTP.instances == []


def test_config_endpoint_reports_status(client, monkeypatch):
    for name in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    assert client.get("/api/config").get_json()["configured"] is False

    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "me@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    payload = client.get("/api/config").get_json()

    assert (payload["configured"], payload["host"], payload["from"]) == (
        True,
        "smtp.example.com",
        "me@example.com",
    )
