import email
import imaplib
import logging
import smtplib
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from .interfaces import MessageReceiverInterface, MessageSenderInterface

logger = logging.getLogger(__name__)


class SmtpMessageSender(MessageSenderInterface):
    """Sends outbound emails using Python's standard smtplib."""

    def __init__(
        self,
        smtp_server: str,
        port: int,
        username: str,
        password: str,
        sender_email: str,
    ) -> None:
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password
        self.sender_email = sender_email

    def send_message(self, recipient: str, subject: str, body: str) -> None:
        """Constructs and sends an email via SMTP (SSL or TLS starttls)."""
        logger.info(f"Preparing SMTP email message to: {recipient}")
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        server: smtplib.SMTP | smtplib.SMTP_SSL
        if self.port == 465:
            logger.debug("Connecting via SMTP SSL")
            server = smtplib.SMTP_SSL(self.smtp_server, self.port, timeout=15)
        else:
            logger.debug("Connecting via SMTP with STARTTLS")
            server = smtplib.SMTP(self.smtp_server, self.port, timeout=15)
            server.starttls()

        try:
            if self.username and self.password:
                server.login(self.username, self.password)
            server.send_message(msg)
            logger.info("Email message sent successfully.")
        except Exception as e:
            logger.error(f"SMTP delivery failed: {e}")
            raise
        finally:
            try:
                server.quit()
            except Exception:
                pass


class ImapMessageReceiver(MessageReceiverInterface):
    """Polls and retrieves emails using Python's standard imaplib."""

    def __init__(
        self, imap_server: str, port: int, username: str, password: str
    ) -> None:
        self.imap_server = imap_server
        self.port = port
        self.username = username
        self.password = password

    def get_latest_messages(self, sender_filter: str) -> list[dict[str, Any]]:
        """Retrieves up to 10 latest emails sent by the authorized sender_filter.

        Returns:
            A list of dicts: [{'id': str, 'sender': str, 'subject': str, 'body': str}]
        """
        logger.debug(f"Connecting to IMAP server: {self.imap_server}:{self.port}")
        mail: imaplib.IMAP4 | imaplib.IMAP4_SSL
        if self.port == 993:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.port, timeout=15)
        else:
            mail = imaplib.IMAP4(self.imap_server, self.port, timeout=15)

        messages: list[dict[str, Any]] = []
        try:
            mail.login(self.username, self.password)
            mail.select("inbox")

            # Search for messages originating from the authorized email filter
            search_query = f'(FROM "{sender_filter}")'
            logger.debug(f"Performing IMAP search: {search_query}")
            status, response = mail.search(None, search_query)
            if status != "OK" or not response[0]:
                return []

            mail_ids = response[0].split()
            # Inspect the latest 10 matches
            for mail_id in mail_ids[-10:]:
                try:
                    status, data = mail.fetch(mail_id, "(RFC822)")
                    if status != "OK" or not data:
                        continue

                    if not isinstance(data[0], tuple):
                        continue
                    raw_email = data[0][1]
                    if not isinstance(raw_email, bytes):
                        continue

                    msg = email.message_from_bytes(raw_email)

                    # Extract & decode subject header
                    subject_header = msg["Subject"] or ""
                    decoded_parts = decode_header(subject_header)
                    subject = ""
                    for part, encoding in decoded_parts:
                        if isinstance(part, bytes):
                            subject += part.decode(encoding or "utf-8", errors="ignore")
                        else:
                            subject += part

                    # Extract body text
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if (
                                content_type == "text/plain"
                                and "attachment" not in content_disposition
                            ):
                                payload = part.get_payload(decode=True)
                                if isinstance(payload, bytes):
                                    body = payload.decode(errors="ignore")
                                    break
                    else:
                        payload = msg.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            body = payload.decode(errors="ignore")

                    messages.append(
                        {
                            "id": mail_id.decode("utf-8"),
                            "sender": msg.get("From", ""),
                            "subject": subject,
                            "body": body.strip(),
                        }
                    )
                except Exception as ex:
                    logger.warning(f"Error parsing IMAP message ID {mail_id}: {ex}")
        except Exception as e:
            logger.error(f"IMAP retrieval failed: {e}")
            raise
        finally:
            try:
                mail.close()
            except Exception:
                pass
            try:
                mail.logout()
            except Exception:
                pass

        return messages


class TelegramMessageSender(MessageSenderInterface):
    """Sends outbound Telegram messages to a specific Chat ID using standard HTTP requests."""

    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token

    def send_message(self, recipient: str, subject: str, body: str) -> None:
        """Sends a text message using the Telegram Bot API sendMessage endpoint."""
        import requests  # type: ignore[import-untyped]

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        # Format the text with the subject and body
        text = f"[{subject}]\n{body}"
        payload = {
            "chat_id": recipient,
            "text": text,
        }

        logger.info(f"Sending Telegram message to chat: {recipient}")
        try:
            response = requests.post(url, json=payload, timeout=15)
            if not response.ok:
                logger.error(f"Telegram API response failed. Status: {response.status_code}, Body: {response.text}")
            response.raise_for_status()
            logger.info("Telegram message sent successfully.")
        except Exception as e:
            logger.error(f"Telegram delivery failed: {e}")
            raise


class TelegramMessageReceiver(MessageReceiverInterface):
    """Retrieves inbound Telegram messages using the getUpdates endpoint, tracking update offsets."""

    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token
        self.offset: int | None = None

    def get_latest_messages(self, sender_filter: str) -> list[dict[str, Any]]:
        """Retrieves incoming messages matching the designated chat_id filter.

        Automatically advances the internal offset to acknowledge read messages.
        """
        import requests

        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        params: dict[str, Any] = {"timeout": 0}
        if self.offset is not None:
            params["offset"] = self.offset

        logger.debug(f"Retrieving Telegram updates with offset: {self.offset}")
        try:
            response = requests.get(url, params=params, timeout=15)
            if not response.ok:
                logger.error(f"Telegram getUpdates API failed. Status: {response.status_code}, Body: {response.text}")
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Telegram getUpdates failed: {e}")
            raise

        if not data.get("ok"):
            logger.error(f"Telegram API response is not OK: {data}")
            return []

        updates = data.get("result", [])
        messages: list[dict[str, Any]] = []
        highest_update_id = -1

        for update in updates:
            up_id = update.get("update_id")
            if isinstance(up_id, int) and up_id > highest_update_id:
                highest_update_id = up_id

            msg_obj = update.get("message")
            if not msg_obj or not isinstance(msg_obj, dict):
                continue

            chat = msg_obj.get("chat")
            if not chat or not isinstance(chat, dict):
                continue

            chat_id = chat.get("id")
            if chat_id is None:
                continue

            # Check if chat ID matches sender filter
            if str(chat_id) != str(sender_filter):
                continue

            text = msg_obj.get("text", "")
            messages.append({
                "id": str(up_id),
                "sender": str(chat_id),
                "subject": "Telegram",
                "body": text,
            })

        if highest_update_id != -1:
            self.offset = highest_update_id + 1

        return messages

