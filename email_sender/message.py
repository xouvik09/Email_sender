from email.message import EmailMessage
from pathlib import Path
from string import Template


class TemplateError(Exception):
    """Raised when a template cannot be rendered with the given context."""


def render(template: str, context: dict[str, str]) -> str:
    """Substitute ``$name`` / ``${name}`` placeholders in ``template``."""
    try:
        return Template(template).substitute(context)
    except KeyError as exc:
        raise TemplateError(f"Missing template variable: {exc.args[0]}") from exc
    except ValueError as exc:
        raise TemplateError(f"Invalid template placeholder: {exc}") from exc


def build_message(
    subject: str,
    sender: str,
    recipient: str,
    text_body: str,
    html_body: str | None = None,
    context: dict[str, str] | None = None,
    attachments: list[str | Path] | None = None,
) -> EmailMessage:
    context = context or {}
    message = EmailMessage()
    message["Subject"] = render(subject, context)
    message["From"] = sender
    message["To"] = recipient
    message.set_content(render(text_body, context))
    if html_body:
        message.add_alternative(render(html_body, context), subtype="html")

    for attachment in attachments or []:
        path = Path(attachment)
        if not path.is_file():
            raise FileNotFoundError(f"Attachment not found: {path}")
        message.add_attachment(
            path.read_bytes(),
            maintype="application",
            subtype="octet-stream",
            filename=path.name,
        )

    return message
