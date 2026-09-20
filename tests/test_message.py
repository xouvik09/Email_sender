import pytest

from email_sender.message import (
    Recipient,
    RecipientError,
    build_message,
    load_recipients,
    render,
)


def write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_load_recipients_with_header(tmp_path):
    path = write(
        tmp_path, "r.csv", "email,name\na@example.com,Ann\nb@example.com,Bob\n"
    )
    recipients = load_recipients(path)
    assert [r.email for r in recipients] == ["a@example.com", "b@example.com"]
    assert recipients[0].fields == {"name": "Ann"}


def test_load_recipients_single_column(tmp_path):
    path = write(tmp_path, "r.csv", "a@example.com\n\nb@example.com\n")
    assert [r.email for r in load_recipients(path)] == [
        "a@example.com",
        "b@example.com",
    ]


def test_load_recipients_rejects_invalid(tmp_path):
    path = write(tmp_path, "r.csv", "email\nnot-an-email\n")
    with pytest.raises(RecipientError):
        load_recipients(path)


def test_load_recipients_rejects_empty(tmp_path):
    path = write(tmp_path, "r.csv", "\n")
    with pytest.raises(RecipientError):
        load_recipients(path)


def test_render_keeps_unknown_placeholders():
    assert render("Hi {{ name }} {{ other }}", {"name": "Ann"}) == "Hi Ann {{ other }}"


def test_build_message_personalizes_and_attaches(tmp_path):
    attachment = tmp_path / "note.txt"
    attachment.write_text("hello", encoding="utf-8")
    message = build_message(
        subject="Hi {{ name }}",
        from_address="me@example.com",
        recipient=Recipient("a@example.com", {"name": "Ann"}),
        text="Dear {{ name }}",
        html="<p>Dear {{ name }}</p>",
        attachments=[attachment],
        reply_to="reply@example.com",
    )
    assert message["Subject"] == "Hi Ann"
    assert message["To"] == "a@example.com"
    assert message["Reply-To"] == "reply@example.com"
    body = message.as_string()
    assert "Dear Ann" in body
    assert "<p>Dear Ann</p>" in body
    assert "note.txt" in body
