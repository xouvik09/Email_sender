import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_SSL_PORT = 465
DEFAULT_STARTTLS_PORT = 587


class ConfigError(Exception):
    """Raised when the SMTP configuration is missing or inconsistent."""


@dataclass(frozen=True)
class SMTPConfig:
    host: str
    username: str
    password: str
    port: int = DEFAULT_SSL_PORT
    use_ssl: bool = True
    sender: str = ""
    sender_name: str = ""

    @property
    def from_address(self) -> str:
        address = self.sender or self.username
        if self.sender_name:
            return f"{self.sender_name} <{address}>"
        return address

    @classmethod
    def from_env(cls, env_file: str | None = None) -> "SMTPConfig":
        load_dotenv(env_file) if env_file else load_dotenv()

        missing = [
            name
            for name in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD")
            if not os.environ.get(name)
        ]
        if missing:
            raise ConfigError(
                "Missing required environment variables: "
                + ", ".join(missing)
                + ". Copy .env.example to .env and fill it in."
            )

        use_ssl = _parse_bool(os.environ.get("SMTP_USE_SSL"), default=True)
        default_port = DEFAULT_SSL_PORT if use_ssl else DEFAULT_STARTTLS_PORT
        port_value = os.environ.get("SMTP_PORT")
        try:
            port = int(port_value) if port_value else default_port
        except ValueError as exc:
            raise ConfigError(f"SMTP_PORT must be an integer, got {port_value!r}") from exc

        return cls(
            host=os.environ["SMTP_HOST"],
            username=os.environ["SMTP_USERNAME"],
            password=os.environ["SMTP_PASSWORD"],
            port=port,
            use_ssl=use_ssl,
            sender=os.environ.get("SMTP_SENDER", ""),
            sender_name=os.environ.get("SMTP_SENDER_NAME", ""),
        )


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
