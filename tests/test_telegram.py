from unittest.mock import MagicMock, patch

import pytest
import requests

from smart_alarm.messaging import TelegramMessageReceiver, TelegramMessageSender


def test_telegram_sender_success() -> None:
    sender = TelegramMessageSender(bot_token="test_token")

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        sender.send_message("12345", "Test Subject", "Test Body")

        mock_post.assert_called_once_with(
            "https://api.telegram.org/bottest_token/sendMessage",
            json={
                "chat_id": "12345",
                "text": "[Test Subject]\nTest Body",
            },
            timeout=15,
        )


def test_telegram_sender_failure() -> None:
    sender = TelegramMessageSender(bot_token="test_token")

    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.RequestException("API Error")

        with pytest.raises(requests.RequestException):
            sender.send_message("12345", "Test Subject", "Test Body")


def test_telegram_receiver_get_messages() -> None:
    receiver = TelegramMessageReceiver(bot_token="test_token")
    assert receiver.offset is None

    # Mocking first call: no offset, returns some updates
    mock_api_response = {
        "ok": True,
        "result": [
            {
                "update_id": 100,
                "message": {
                    "message_id": 1,
                    "chat": {"id": 12345},
                    "text": "Ignored message because sender doesn't match",
                },
            },
            {
                "update_id": 101,
                "message": {
                    "message_id": 2,
                    "chat": {"id": 99999},
                    "text": "Correct message",
                },
            },
            {
                "update_id": 102,
                "message": {
                    "message_id": 3,
                    # No text message or unrelated update type
                },
            },
        ],
    }

    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_api_response
        mock_get.return_value = mock_response

        # We query filtering by "99999"
        messages = receiver.get_latest_messages("99999")

        mock_get.assert_called_once_with(
            "https://api.telegram.org/bottest_token/getUpdates",
            params={"timeout": 0},
            timeout=15,
        )

        assert len(messages) == 1
        assert messages[0] == {
            "id": "101",
            "sender": "99999",
            "subject": "Telegram",
            "body": "Correct message",
        }

        # Internal offset should be advanced to highest update_id + 1
        assert receiver.offset == 103

    # Now verify the next call uses the updated offset
    with patch("requests.get") as mock_get2:
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {"ok": True, "result": []}
        mock_get2.return_value = mock_response2

        messages2 = receiver.get_latest_messages("99999")
        assert len(messages2) == 0
        mock_get2.assert_called_once_with(
            "https://api.telegram.org/bottest_token/getUpdates",
            params={"timeout": 0, "offset": 103},
            timeout=15,
        )
