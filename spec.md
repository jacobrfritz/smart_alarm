Project Specification: Sonos Math Alarm

1. Project Overview

Name: Sonos Math Alarm
Description: A Python-based alarm clock system triggered via a cron job. Upon triggering, it plays audio through a Sonos system and sends a text/email containing a randomly generated math problem. The alarm continues to play until the user replies with the correct answer or a predefined timeout is reached.
Core Technologies: Python, Sonos API (e.g., soco), Email/SMS Gateway (e.g., SMTP or Twilio), Cron.
Design Philosophy: Object-Oriented Programming (OOP), Test-Driven Development (TDD), SOLID principles.

2. Core Workflows

2.1 Triggering the Alarm (Cron Job)

The system is initiated by an external cron job scheduling tool (e.g., standard Linux cron).

The cron job calls the main Python entry point script.

2.2 Alarm Activation

When executed, the script identifies the target Sonos speaker/group.

It initiates playback of a predefined audio track or playlist.

Concurrently, a math problem is generated.

The system sends an email (or email-to-SMS) containing the math problem to a configured recipient.

2.3 User Interaction and Verification

The system enters a state where it listens for incoming email replies.

It periodically checks the inbox for messages originating from the authorized user.

When a response is received, the system parses it for the numeric answer.

It evaluates the user's answer against the correct answer for the generated problem.

2.4 Resolution

Success: If the correct answer is received, the system sends a "stop" command to the Sonos speaker and exits cleanly.

Timeout: If a predefined timeout duration elapses without a correct answer, the system sends a "stop" command to the Sonos speaker and logs the timeout event before exiting.

Failure: If an incorrect answer is received, the alarm continues, and the system may (optionally) send a message indicating an incorrect attempt.

3. System Architecture & Component Design (SOLID Focus)

The system will be designed with loosely coupled, single-responsibility components to facilitate TDD and maintainability.

3.1 Interfaces/Abstract Base Classes (Dependency Inversion)

AudioControllerInterface: Defines methods like play(audio_uri), stop(), get_status().

MessageSenderInterface: Defines a method send_message(recipient, subject, body).

MessageReceiverInterface: Defines a method get_latest_messages(sender_filter).

MathProblemGeneratorInterface: Defines a method generate_problem() -> (str, float).

3.2 Concrete Implementations

SonosController (Implements AudioControllerInterface): Uses a library like soco to control the physical Sonos hardware.

SmtpMessageSender (Implements MessageSenderInterface): Uses Python's smtplib to send the math problem via email/email-to-SMS.

ImapMessageReceiver (Implements MessageReceiverInterface): Uses Python's imaplib to poll an inbox for the user's reply.

BasicMathProblemGenerator (Implements MathProblemGeneratorInterface): Generates random arithmetic problems (e.g., "What is 15 + 27?").

3.3 Core Logic

AlarmManager: The central orchestrator. It depends on abstractions (AudioControllerInterface, etc.), not concrete implementations. It handles the main loop, timeout logic, and coordinates the interactions between generating the problem, starting the audio, sending the message, checking for replies, and verifying the answer.

4. Test-Driven Development (TDD) Strategy

The project will follow a strict Red-Green-Refactor cycle.

4.1 Unit Testing (Pytest)

Mocking: All external dependencies (Sonos hardware, network connections for email) will be rigorously mocked during unit testing to ensure tests run fast and deterministically.

Test Cases:

TestBasicMathProblemGenerator: Verify it produces valid strings and correct answers.

TestAlarmManager: Verify it calls play() on the audio controller when started. Verify it calls send_message() with the correct problem. Verify it calls stop() upon receiving the correct answer or hitting the timeout. Verify it does not call stop() on an incorrect answer.

TestSmtpMessageSender (with mocked SMTP server): Verify correct message formatting.

4.2 Integration Testing (Optional/Later Phase)

Tests involving actual connections to test email accounts to verify IMAP/SMTP functionality.

Tests using a Sonos stub or a dedicated test speaker (if available).

5. Requirements & Dependencies

Python Version: Python 3.9+

Libraries (Requirements.txt):

soco (Sonos control)

pytest (Testing framework)

pytest-mock (Mocking library)

(Standard Library): smtplib, email, imaplib, math, random, time

Configuration: A configuration file (e.g., .env or YAML) to store:

Sonos speaker IP or name

SMTP server address, port, username, password

IMAP server address, port, username, password

Authorized recipient email/phone number

Timeout duration

6. Open Questions & Refinements

Complexity of Math: Should the math problems be configurable in difficulty? (e.g., simple addition vs. algebra).

Notification of Failure: If the user sends an incorrect answer, should the system reply with a "Try again" message?

Polling Frequency: How often should the ImapMessageReceiver check the inbox for replies? (Needs to be balanced between responsiveness and server load).