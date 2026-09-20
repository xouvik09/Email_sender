import pytest

from email_sender.message import TemplateError, build_message, render


def test_render_substitutes_context():
    assert render("Hi $name", {"name": "Ada"}) == "Hi Ada"


def test_render_reports_missing_variable():
    with pytest.raises(TemplateError, match="name"):
        render("Hi $name", {})


def test_build_message_sets_headers_and_bodies():
    message = build_message(
        subject="Hello $name",
        sender="me@example.com",
        recipient="ada@example.com",
        text_body="Hi $name",
        html_body="<p>Hi $name</p>",
        context={"name": "Ada"},
    )

    assert message["Subject"] == "Hello Ada"
    assert message["From"] == "me@example.com"
    assert message["To"] == "ada@example.com"
    assert message.get_body(("plain",)).get_content().strip() == "Hi Ada"
    assert message.get_body(("html",)).get_content().strip() == "<p>Hi Ada</p>"


def test_build_message_attaches_files(tmp_path):
    attachment = tmp_path / "report.pdf"
    attachment.write_bytes(b"%PDF-1.4")

    message = build_message(
        subject="s",
        sender="me@example.com",
        recipient="ada@example.com",
        text_body="body",
        attachments=[attachment],
    )

    names = [part.get_filename() for part in message.iter_attachments()]
    assert names == ["report.pdf"]


def test_build_message_rejects_missing_attachment(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_message(
            subject="s",
            sender="me@example.com",
            recipient="ada@example.com",
            text_body="body",
            attachments=[tmp_path / "nope.pdf"],
        )
