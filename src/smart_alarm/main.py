from .config import Config
from .interfaces import MessageReceiverInterface, MessageSenderInterface
from .manager import AlarmManager
from .math_generator import BasicMathProblemGenerator
from .messaging import (
    ImapMessageReceiver,
    SmtpMessageSender,
    TelegramMessageReceiver,
    TelegramMessageSender,
)
from .sonos import SonosController


def run_alarm(config: Config) -> bool:
    """Binds all subsystems into AlarmManager and executes the monitoring sequence.

    Returns:
        bool: True if resolved correctly by user, False if timed out.
    """
    audio_controller = SonosController(config.sonos_speaker, volume=config.sonos_volume)
    problem_generator = BasicMathProblemGenerator()

    message_sender: MessageSenderInterface
    message_receiver: MessageReceiverInterface

    if config.provider == "telegram":
        message_sender = TelegramMessageSender(bot_token=config.telegram_bot_token)
        message_receiver = TelegramMessageReceiver(bot_token=config.telegram_bot_token)
        recipient = config.telegram_chat_id
    else:
        message_sender = SmtpMessageSender(
            smtp_server=config.smtp_server,
            port=config.smtp_port,
            username=config.smtp_username,
            password=config.smtp_password,
            sender_email=config.sender_email,
        )
        message_receiver = ImapMessageReceiver(
            imap_server=config.imap_server,
            port=config.imap_port,
            username=config.imap_username,
            password=config.imap_password,
        )
        recipient = config.recipient_email

    manager = AlarmManager(
        audio_controller=audio_controller,
        message_sender=message_sender,
        message_receiver=message_receiver,
        problem_generator=problem_generator,
        recipient=recipient,
        audio_uri=config.audio_uri,
        timeout_seconds=config.timeout_seconds,
        check_interval_seconds=config.check_interval_seconds,
        reply_on_failure=config.reply_on_failure,
    )

    return manager.start_alarm()

