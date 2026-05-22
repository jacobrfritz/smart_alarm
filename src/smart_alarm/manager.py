import logging
import re
import time

from .interfaces import (
    AudioControllerInterface,
    MathProblemGeneratorInterface,
    MessageReceiverInterface,
    MessageSenderInterface,
)

logger = logging.getLogger(__name__)


class AlarmManager:
    """Orchestrates the Sonos Math Alarm lifecycle, polling, and verification logic."""

    def __init__(
        self,
        audio_controller: AudioControllerInterface,
        message_sender: MessageSenderInterface,
        message_receiver: MessageReceiverInterface,
        problem_generator: MathProblemGeneratorInterface,
        recipient: str,
        audio_uri: str,
        timeout_seconds: int = 600,
        check_interval_seconds: int = 10,
        reply_on_failure: bool = True,
    ) -> None:
        self.audio_controller = audio_controller
        self.message_sender = message_sender
        self.message_receiver = message_receiver
        self.problem_generator = problem_generator
        self.recipient = recipient
        self.audio_uri = audio_uri
        self.timeout_seconds = timeout_seconds
        self.check_interval_seconds = check_interval_seconds
        self.reply_on_failure = reply_on_failure

    def start_alarm(self) -> bool:
        """Triggers the alarm sequence.

        Begins playback, delivers the math problem, and loops checking for email response.
        Stops playback and returns True if solved, or False if the timeout is reached.
        """
        logger.info("Initializing Sonos Math Alarm activation sequence...")

        # 1. Generate the initial math problem
        problem_text, correct_answer = self.problem_generator.generate_problem()
        logger.info(
            f"Generated challenge problem: '{problem_text}' (Target: {correct_answer})"
        )

        # 2. Trigger Sonos sound playback
        logger.info(f"Initiating speaker audio stream: {self.audio_uri}")
        try:
            self.audio_controller.play(self.audio_uri)
        except Exception as e:
            logger.error(
                f"Failed to play audio on Sonos hardware: {e}. Proceeding with message alert."
            )

        # 3. Send initial email notification
        subject = "Sonos Math Alarm - WAKE UP!"
        body = (
            "Time to wake up! To silence the Sonos alarm speaker, "
            f"reply to this email with the correct answer to this problem:\n\n{problem_text}"
        )
        try:
            self.message_sender.send_message(self.recipient, subject, body)
        except Exception as e:
            logger.error(f"Initial email transmission failed: {e}")

        # 4. Initialize polled message ID checklist to ignore pre-existing emails
        last_checked_msg_ids: set[str] = set()
        try:
            initial_msgs = self.message_receiver.get_latest_messages(self.recipient)
            last_checked_msg_ids = {msg["id"] for msg in initial_msgs if "id" in msg}
            logger.debug(
                f"Cached {len(last_checked_msg_ids)} pre-existing message IDs to ignore."
            )
        except Exception as e:
            logger.warning(
                f"Could not scan initial mail state: {e}. Will treat all new queries as replies."
            )

        # 5. Monitoring and Verification Loop
        start_time = time.time()
        solved = False

        logger.info("Alarm tracking active. Entering email inbox verification loop...")
        while time.time() - start_time < self.timeout_seconds:
            # Check Sonos status (ensure speaker is playing)
            # Sonos controllers can optionally restart if stopped externally,
            # but per spec we mainly poll for user answers and check timeouts.

            try:
                latest_msgs = self.message_receiver.get_latest_messages(self.recipient)

                # Search for any new replies
                for msg in latest_msgs:
                    msg_id = msg.get("id")
                    if msg_id and msg_id not in last_checked_msg_ids:
                        last_checked_msg_ids.add(msg_id)

                        body_text = msg.get("body", "")
                        logger.info(
                            f"Intercepted new incoming message reply body:\n{body_text}"
                        )

                        parsed_ans = self._parse_answer(body_text)
                        if parsed_ans is not None:
                            logger.info(
                                f"Parsed numeric answer: {parsed_ans} (Expected: {correct_answer})"
                            )

                            if parsed_ans == correct_answer:
                                logger.info(
                                    "Matching answer received! Solving complete."
                                )
                                solved = True
                                break
                            else:
                                logger.info("Incorrect answer matched.")
                                if self.reply_on_failure:
                                    # Generate a NEW math problem to challenge the user again
                                    new_problem, new_answer = (
                                        self.problem_generator.generate_problem()
                                    )
                                    logger.info(
                                        f"Regenerating challenge problem: '{new_problem}' (Target: {new_answer})"
                                    )

                                    # Update expected state
                                    correct_answer = new_answer
                                    problem_text = new_problem

                                    # Reply notifying failure and presenting new problem
                                    reply_subject = "Incorrect Answer - Try Again!"
                                    reply_body = (
                                        f"That answer ({parsed_ans}) is incorrect. The Sonos speaker will keep ringing.\n"
                                        f"Please solve this new problem instead:\n\n{new_problem}"
                                    )
                                    self.message_sender.send_message(
                                        self.recipient, reply_subject, reply_body
                                    )
            except Exception as e:
                logger.error(f"Error checking email messages during loop step: {e}")

            if solved:
                break

            time.sleep(self.check_interval_seconds)

        # 6. Stop audio play and report outcome
        logger.info("Initiating speaker silencing cleanup...")
        try:
            self.audio_controller.stop()
        except Exception as e:
            logger.error(f"Failed to silence Sonos speaker playback: {e}")

        if solved:
            logger.info(
                "Alarm deactivated cleanly: User successfully resolved the math problem."
            )
            return True
        else:
            logger.warning(
                f"Alarm timed out after {self.timeout_seconds} seconds without correct resolution."
            )
            return False

    def _parse_answer(self, body: str) -> int | None:
        """Helper to parse a single integer answer from the email body text.

        Isolates the first actual reply line of the email (ignoring quote lines starting with '>')
        and extracts the first integer found.
        """
        if not body:
            return None

        for line in body.splitlines():
            line = line.strip()
            # Ignore standard email quoting lines (replies containing original text)
            if not line or line.startswith(">"):
                continue

            # Look for the first integer block
            match = re.search(r"[-+]?\d+", line)
            if match:
                try:
                    return int(match.group())
                except ValueError:
                    pass
            # Stop parsing after evaluating the first line containing candidate text
            break
        return None
