from abc import ABC, abstractmethod
from typing import Any


class AudioControllerInterface(ABC):
    """Interface for controlling audio playback on a smart speaker or audio system."""

    @abstractmethod
    def play(self, audio_uri: str) -> None:
        """Starts audio playback of a specified URI track or stream."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops all active audio playback."""
        pass

    @abstractmethod
    def get_status(self) -> str:
        """Retrieves the current playback status (e.g., 'PLAYING', 'STOPPED', 'PAUSED')."""
        pass


class MessageSenderInterface(ABC):
    """Interface for sending outbound messages (emails or email-to-SMS alerts)."""

    @abstractmethod
    def send_message(self, recipient: str, subject: str, body: str) -> None:
        """Sends a message to the target recipient."""
        pass


class MessageReceiverInterface(ABC):
    """Interface for polling and retrieving inbound messages."""

    @abstractmethod
    def get_latest_messages(self, sender_filter: str) -> list[dict[str, Any]]:
        """Checks for latest inbound messages filtered by the sender's address.

        Returns:
            A list of dictionary objects representing message entries, containing fields:
            - 'id': str
            - 'sender': str
            - 'subject': str
            - 'body': str
        """
        pass


class MathProblemGeneratorInterface(ABC):
    """Interface for generating randomized mathematical problem equations."""

    @abstractmethod
    def generate_problem(self) -> tuple[str, int]:
        """Generates a random arithmetic equation.

        Returns:
            A tuple of (equation_string, integer_answer).
        """
        pass
