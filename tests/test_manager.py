from unittest.mock import MagicMock, call

from smart_alarm.interfaces import (
    AudioControllerInterface,
    MathProblemGeneratorInterface,
    MessageReceiverInterface,
    MessageSenderInterface,
)
from smart_alarm.manager import AlarmManager


def test_parse_answer() -> None:
    # We will instantiate a dummy manager with None dependencies just to test the helper parser
    manager = AlarmManager(
        audio_controller=None,  # type: ignore
        message_sender=None,  # type: ignore
        message_receiver=None,  # type: ignore
        problem_generator=None,  # type: ignore
        recipient="test@recipient.com",
        audio_uri="http://test.mp3",
    )

    # Simple plain matches
    assert manager._parse_answer("42") == 42
    assert manager._parse_answer("  +84  ") == 84
    assert manager._parse_answer("-105") == -105

    # Text surrounding numbers on the first line
    assert manager._parse_answer("The answer is 123!") == 123
    assert manager._parse_answer("999 - is the number") == 999

    # Multiline with email reply quotes (lines starting with '>')
    email_body = "> What is 100 + 200?\n> From sender\n\n300\nSome signature here\n"
    assert manager._parse_answer(email_body) == 300

    # No numbers present
    assert manager._parse_answer("hello world") is None
    assert manager._parse_answer("") is None


def test_alarm_manager_success_flow() -> None:
    # 1. Setup mock interfaces
    audio_mock = MagicMock(spec=AudioControllerInterface)
    sender_mock = MagicMock(spec=MessageSenderInterface)
    receiver_mock = MagicMock(spec=MessageReceiverInterface)
    generator_mock = MagicMock(spec=MathProblemGeneratorInterface)

    # 2. Configure mock outputs
    generator_mock.generate_problem.return_value = ("What is 50 + 50?", 100)

    # First get_latest_messages call returns no initial emails to cache
    # Second get_latest_messages call returns the correct answer
    receiver_mock.get_latest_messages.side_effect = [
        [],  # initial check to cache IDs
        [{"id": "msg_001", "sender": "user@test.com", "body": "100"}],  # poll check
    ]

    manager = AlarmManager(
        audio_controller=audio_mock,
        message_sender=sender_mock,
        message_receiver=receiver_mock,
        problem_generator=generator_mock,
        recipient="user@test.com",
        audio_uri="http://alarm.mp3",
        timeout_seconds=5,
        check_interval_seconds=1,
    )

    # 3. Trigger alarm execution
    success = manager.start_alarm()

    assert success is True

    # 4. Verify mock calls
    generator_mock.generate_problem.assert_called_once()
    audio_mock.play.assert_called_once_with("http://alarm.mp3")
    sender_mock.send_message.assert_called_once_with(
        "user@test.com",
        "Sonos Math Alarm - WAKE UP!",
        "Time to wake up! To silence the Sonos alarm speaker, reply to this email with the correct answer to this problem:\n\nWhat is 50 + 50?",
    )
    audio_mock.stop.assert_called_once()


def test_alarm_manager_timeout_flow() -> None:
    audio_mock = MagicMock(spec=AudioControllerInterface)
    sender_mock = MagicMock(spec=MessageSenderInterface)
    receiver_mock = MagicMock(spec=MessageReceiverInterface)
    generator_mock = MagicMock(spec=MathProblemGeneratorInterface)

    generator_mock.generate_problem.return_value = ("What is 10 * 10?", 100)
    receiver_mock.get_latest_messages.return_value = []  # No incoming replies

    manager = AlarmManager(
        audio_controller=audio_mock,
        message_sender=sender_mock,
        message_receiver=receiver_mock,
        problem_generator=generator_mock,
        recipient="user@test.com",
        audio_uri="http://alarm.mp3",
        timeout_seconds=2,  # Short timeout for testing
        check_interval_seconds=1,
    )

    success = manager.start_alarm()

    assert success is False
    audio_mock.play.assert_called_once()
    audio_mock.stop.assert_called_once()


def test_alarm_manager_incorrect_answer_regeneration_flow() -> None:
    audio_mock = MagicMock(spec=AudioControllerInterface)
    sender_mock = MagicMock(spec=MessageSenderInterface)
    receiver_mock = MagicMock(spec=MessageReceiverInterface)
    generator_mock = MagicMock(spec=MathProblemGeneratorInterface)

    # Mock generator returns:
    # First: "What is 20 + 20?" (answer 40)
    # Second: "What is 30 * 30?" (answer 900)
    generator_mock.generate_problem.side_effect = [
        ("What is 20 + 20?", 40),
        ("What is 30 * 30?", 900),
    ]

    # Mock receiver calls:
    # 1. Initial cached state -> empty
    # 2. First poll -> returns wrong answer "15"
    # 3. Second poll -> returns correct new answer "900"
    receiver_mock.get_latest_messages.side_effect = [
        [],  # initial setup cache
        [
            {"id": "msg_001", "sender": "user@test.com", "body": "15"}
        ],  # first reply (wrong)
        [
            {"id": "msg_002", "sender": "user@test.com", "body": "900"}
        ],  # second reply (correct new problem)
    ]

    manager = AlarmManager(
        audio_controller=audio_mock,
        message_sender=sender_mock,
        message_receiver=receiver_mock,
        problem_generator=generator_mock,
        recipient="user@test.com",
        audio_uri="http://alarm.mp3",
        timeout_seconds=10,
        check_interval_seconds=1,
        reply_on_failure=True,
    )

    success = manager.start_alarm()

    # Must resolve successfully after solving the regenerated problem
    assert success is True

    # Verify problem was generated twice
    assert generator_mock.generate_problem.call_count == 2

    # Verify both email sends happened
    # 1. Initial Wakeup Challenge
    # 2. Failure notice containing second challenge
    assert sender_mock.send_message.call_count == 2
    sender_mock.send_message.assert_has_calls(
        [
            call(
                "user@test.com",
                "Sonos Math Alarm - WAKE UP!",
                "Time to wake up! To silence the Sonos alarm speaker, reply to this email with the correct answer to this problem:\n\nWhat is 20 + 20?",
            ),
            call(
                "user@test.com",
                "Incorrect Answer - Try Again!",
                "That answer (15) is incorrect. The Sonos speaker will keep ringing.\nPlease solve this new problem instead:\n\nWhat is 30 * 30?",
            ),
        ]
    )

    audio_mock.play.assert_called_once()
    audio_mock.stop.assert_called_once()
