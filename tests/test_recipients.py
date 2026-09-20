import pytest

from email_sender.recipients import RecipientError, read_recipients


def write_csv(tmp_path, content):
    path = tmp_path / "email.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_reads_bare_single_column(tmp_path):
    path = write_csv(tmp_path, "a@example.com\nb@example.com\n")

    recipients = read_recipients(path)

    assert [r.email for r in recipients] == ["a@example.com", "b@example.com"]
    assert recipients[0].context == {"email": "a@example.com"}


def test_reads_header_columns_as_template_fields(tmp_path):
    path = write_csv(tmp_path, "name,email\nAda,ada@example.com\n")

    recipients = read_recipients(path)

    assert recipients[0].context == {"email": "ada@example.com", "name": "Ada"}


def test_skips_invalid_and_duplicate_rows(tmp_path):
    path = write_csv(tmp_path, "a@example.com\nnot-an-email\n\nA@example.com\nb@example.com\n")

    recipients = read_recipients(path)

    assert [r.email for r in recipients] == ["a@example.com", "b@example.com"]


def test_raises_on_invalid_when_not_skipping(tmp_path):
    path = write_csv(tmp_path, "a@example.com\nbroken\n")

    with pytest.raises(RecipientError):
        read_recipients(path, skip_invalid=False)


def test_raises_when_no_valid_addresses(tmp_path):
    path = write_csv(tmp_path, "nope\n")

    with pytest.raises(RecipientError):
        read_recipients(path)


def test_raises_on_missing_file(tmp_path):
    with pytest.raises(RecipientError):
        read_recipients(tmp_path / "missing.csv")
