import os
from pathlib import Path

import pytest

from smart_alarm.config import Config, load_dotenv


def test_load_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Set up a temporary mock .env file
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SONOS_SPEAKER=Living Room Test\n"
        "TIMEOUT_SECONDS=300\n"
        'SENDER_EMAIL="quoted_sender@test.com"\n'
        "# Commented key should be ignored\n"
        "# IGNORE_KEY=true\n"
        "INVALID_LINE_NO_EQUALS\n",
        encoding="utf-8",
    )

    # Monkeypatch environmental values to isolate tests
    monkeypatch.setattr(os, "environ", {})

    # Load dotenv from custom temp file
    load_dotenv(str(env_file))

    assert os.environ.get("SONOS_SPEAKER") == "Living Room Test"
    assert os.environ.get("TIMEOUT_SECONDS") == "300"
    assert os.environ.get("SENDER_EMAIL") == "quoted_sender@test.com"
    assert "IGNORE_KEY" not in os.environ


def test_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    # Clear environment variables to test defaults
    monkeypatch.setattr(os, "environ", {})

    config = Config()
    assert config.sonos_speaker == "Living Room"
    assert config.timeout_seconds == 600
    assert config.check_interval_seconds == 10
    assert config.reply_on_failure is True
    assert config.smtp_port == 587
    assert config.imap_port == 993


def test_config_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "environ", {})

    config = Config()
    # Missing crucial variables should trigger a ValueError
    with pytest.raises(ValueError) as exc:
        config.validate()
    assert "Missing required Email configuration variables" in str(exc.value)

    # Injecting parameters should satisfy validation
    monkeypatch.setenv("RECIPIENT_EMAIL", "recipient@test.com")
    monkeypatch.setenv("SENDER_EMAIL", "sender@test.com")
    monkeypatch.setenv("SMTP_USERNAME", "smtp_user")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp_pass")
    monkeypatch.setenv("IMAP_USERNAME", "imap_user")
    monkeypatch.setenv("IMAP_PASSWORD", "imap_pass")

    config = Config()
    # Should complete without throwing exceptions
    config.validate()


def test_config_telegram_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "environ", {})
    monkeypatch.setenv("PROVIDER", "telegram")

    config = Config()
    # Missing crucial Telegram variables should trigger a ValueError
    with pytest.raises(ValueError) as exc:
        config.validate()
    assert "Missing required Telegram configuration variables" in str(exc.value)

    # Injecting parameters should satisfy validation
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-Def")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "987654321")

    config = Config()
    # Should complete without throwing exceptions
    config.validate()

