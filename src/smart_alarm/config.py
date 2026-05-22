import os
from pathlib import Path


def load_dotenv(filepath: str = ".env") -> None:
    """Reads environment variables from a local file and loads them into os.environ.

    Skips existing variables in os.environ to prevent overriding shell environments.
    """
    path = Path(filepath)
    if not path.exists():
        return

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines, comments, and invalid formats
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()

            # Remove enclosing quotes if present
            if val.startswith(('"', "'")) and val.endswith(('"', "'")):
                val = val[1:-1]

            if key not in os.environ:
                os.environ[key] = val


class Config:
    """Strongly-typed validation container for the Sonos Math Alarm configuration."""

    def __init__(self) -> None:
        self.provider: str = os.getenv("PROVIDER", "email").lower()
        self.telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

        self.sonos_speaker: str = os.getenv("SONOS_SPEAKER", "Living Room")
        sonos_vol_str = os.getenv("SONOS_VOLUME", "")
        self.sonos_volume: int | None = int(sonos_vol_str) if sonos_vol_str else None
        self.audio_uri: str = os.getenv(
            "AUDIO_URI",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        )

        self.smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username: str = os.getenv("SMTP_USERNAME", "")
        self.smtp_password: str = os.getenv("SMTP_PASSWORD", "")
        self.sender_email: str = os.getenv("SENDER_EMAIL", "")

        self.imap_server: str = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.imap_port: int = int(os.getenv("IMAP_PORT", "993"))
        self.imap_username: str = os.getenv("IMAP_USERNAME", "")
        self.imap_password: str = os.getenv("IMAP_PASSWORD", "")

        self.recipient_email: str = os.getenv("RECIPIENT_EMAIL", "")
        self.timeout_seconds: int = int(os.getenv("TIMEOUT_SECONDS", "600"))
        self.check_interval_seconds: int = int(
            os.getenv("CHECK_INTERVAL_SECONDS", "10")
        )
        self.reply_on_failure: bool = os.getenv("REPLY_ON_FAILURE", "true").lower() in (
            "true",
            "1",
            "yes",
        )

    def validate(self) -> None:
        """Validates that crucial settings are filled in to run the alarm."""
        if self.provider == "telegram":
            missing = []
            if not self.telegram_bot_token:
                missing.append("TELEGRAM_BOT_TOKEN")
            if not self.telegram_chat_id:
                missing.append("TELEGRAM_CHAT_ID")
            if missing:
                raise ValueError(
                    f"Missing required Telegram configuration variables: {', '.join(missing)}"
                )
        else:
            missing = []
            if not self.recipient_email:
                missing.append("RECIPIENT_EMAIL")
            if not self.sender_email:
                missing.append("SENDER_EMAIL")
            if not self.smtp_username:
                missing.append("SMTP_USERNAME")
            if not self.smtp_password:
                missing.append("SMTP_PASSWORD")
            if not self.imap_username:
                missing.append("IMAP_USERNAME")
            if not self.imap_password:
                missing.append("IMAP_PASSWORD")

            if missing:
                raise ValueError(
                    f"Missing required Email configuration variables: {', '.join(missing)}"
                )
