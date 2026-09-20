import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    pass


def load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file without overriding existing vars."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    username: str
    password: str
    port: int = 465
    use_ssl: bool = True
    sender: str = ""
    sender_name: str = ""

    @property
    def from_address(self) -> str:
        address = self.sender or self.username
        if self.sender_name:
            return f"{self.sender_name} <{address}>"
        return address

    @property
    def envelope_from(self) -> str:
        return self.sender or self.username

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "SmtpConfig":
        env = dict(os.environ if env is None else env)
        missing = [
            name
            for name in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD")
            if not env.get(name)
        ]
        if missing:
            raise ConfigError(
                "Missing required environment variables: " + ", ".join(missing)
            )
        use_ssl = env.get("SMTP_USE_SSL", "true").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        return cls(
            host=env["SMTP_HOST"],
            username=env["SMTP_USERNAME"],
            password=env["SMTP_PASSWORD"],
            port=int(env.get("SMTP_PORT", "465" if use_ssl else "587")),
            use_ssl=use_ssl,
            sender=env.get("SMTP_SENDER", ""),
            sender_name=env.get("SMTP_SENDER_NAME", ""),
        )
