from unittest.mock import MagicMock, patch

from smart_alarm import main
from smart_alarm.config import Config


@patch("smart_alarm.main.SonosController")
@patch("smart_alarm.main.SmtpMessageSender")
@patch("smart_alarm.main.ImapMessageReceiver")
@patch("smart_alarm.main.BasicMathProblemGenerator")
@patch("smart_alarm.main.AlarmManager")
def test_run_alarm_wiring(
    mock_manager_class: MagicMock,
    mock_generator_class: MagicMock,
    mock_receiver_class: MagicMock,
    mock_sender_class: MagicMock,
    mock_sonos_class: MagicMock,
) -> None:
    # Set up valid mock configuration
    config = Config()
    config.recipient_email = "test@recipient.com"
    config.sender_email = "sender@test.com"
    config.smtp_username = "smtp_user"
    config.smtp_password = "smtp_pass"
    config.imap_username = "imap_user"
    config.imap_password = "imap_pass"

    # Configure the instantiated AlarmManager mock
    mock_manager = MagicMock()
    mock_manager.start_alarm.return_value = True
    mock_manager_class.return_value = mock_manager

    # Execute wiring logic
    result = main.run_alarm(config)

    # Assert wiring constructs all components and delegates properly
    assert result is True
    mock_sonos_class.assert_called_once_with(config.sonos_speaker, volume=None)
    mock_sender_class.assert_called_once_with(
        smtp_server=config.smtp_server,
        port=config.smtp_port,
        username=config.smtp_username,
        password=config.smtp_password,
        sender_email=config.sender_email,
    )
    mock_receiver_class.assert_called_once_with(
        imap_server=config.imap_server,
        port=config.imap_port,
        username=config.imap_username,
        password=config.imap_password,
    )
    mock_generator_class.assert_called_once()
    mock_manager_class.assert_called_once()
    mock_manager.start_alarm.assert_called_once()
