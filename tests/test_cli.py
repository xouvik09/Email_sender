from email_sender import cli


def test_cli_dry_run_reports_success(tmp_path, monkeypatch, capsys):
    csv_path = tmp_path / "r.csv"
    csv_path.write_text("email,name\na@example.com,Ann\n", encoding="utf-8")
    text_path = tmp_path / "msg.txt"
    text_path.write_text("Hello {{ name }}", encoding="utf-8")

    for key, value in {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_USERNAME": "me@example.com",
        "SMTP_PASSWORD": "secret",
    }.items():
        monkeypatch.setenv(key, value)

    exit_code = cli.main(
        [
            "--csv",
            str(csv_path),
            "--text",
            str(text_path),
            "--html",
            str(tmp_path / "missing.html"),
            "--env-file",
            str(tmp_path / "missing.env"),
            "--dry-run",
        ]
    )
    assert exit_code == 0
    assert "1/1 messages sent" in capsys.readouterr().out


def test_cli_requires_recipients(tmp_path, monkeypatch, capsys):
    for key in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"):
        monkeypatch.setenv(key, "x@example.com")
    exit_code = cli.main(["--env-file", str(tmp_path / "missing.env")])
    assert exit_code == 2
    assert "No recipients" in capsys.readouterr().err


def test_cli_missing_credentials(tmp_path, monkeypatch, capsys):
    for key in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    exit_code = cli.main(
        ["--to", "a@example.com", "--env-file", str(tmp_path / "missing.env")]
    )
    assert exit_code == 2
    assert "Missing required environment variables" in capsys.readouterr().err
