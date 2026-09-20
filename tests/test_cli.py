import smtplib

import pytest

from email_sender.cli import main
from tests.test_sender import FakeSMTP


@pytest.fixture
def project(tmp_path):
    (tmp_path / "email.csv").write_text("name,email\nAda,ada@example.com\n", encoding="utf-8")
    (tmp_path / "msg.txt").write_text("Hello $name", encoding="utf-8")
    (tmp_path / "msg.html").write_text("<p>Hello $name</p>", encoding="utf-8")
    return tmp_path


def test_dry_run_requires_no_credentials(project, capsys):
    exit_code = main(
        [
            "--csv",
            str(project / "email.csv"),
            "--text",
            str(project / "msg.txt"),
            "--html",
            str(project / "msg.html"),
            "--dry-run",
        ]
    )

    assert exit_code == 0
    assert "would send 1/1 messages" in capsys.readouterr().out


def test_missing_credentials_exit_code(project, monkeypatch, capsys):
    for name in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"):
        monkeypatch.delenv(name, raising=False)

    exit_code = main(
        [
            "--csv",
            str(project / "email.csv"),
            "--text",
            str(project / "msg.txt"),
            "--env-file",
            str(project / "nonexistent.env"),
        ]
    )

    assert exit_code == 2
    assert "SMTP_HOST" in capsys.readouterr().err


def test_missing_recipient_file_exit_code(project, capsys):
    exit_code = main(
        ["--csv", str(project / "nope.csv"), "--text", str(project / "msg.txt"), "--dry-run"]
    )

    assert exit_code == 2
    assert "error" in capsys.readouterr().err


def test_sends_to_inline_recipients(project, monkeypatch, capsys):
    FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "me@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    (project / "plain.txt").write_text("Hello there", encoding="utf-8")

    exit_code = main(
        [
            "--to",
            "one@example.com",
            "--to",
            "two@example.com",
            "--text",
            str(project / "plain.txt"),
            "--html",
            str(project / "missing.html"),
            "--subject",
            "Greetings",
            "--env-file",
            str(project / "nonexistent.env"),
        ]
    )

    assert exit_code == 0
    assert "sent 2/2 messages" in capsys.readouterr().out
    sent = FakeSMTP.instances[0].sent
    assert [m["To"] for m in sent] == ["one@example.com", "two@example.com"]
    assert sent[0]["Subject"] == "Greetings"
