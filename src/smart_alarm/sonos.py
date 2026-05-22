import http.server
import logging
import socket
import socketserver
import threading
from pathlib import Path
from typing import Any

import soco  # type: ignore[import-untyped]

from .interfaces import AudioControllerInterface

logger = logging.getLogger(__name__)


def get_local_ip() -> str:
    """Finds the actual local network interface IP address on the subnet."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a public DNS address to discover local routing interface
        s.connect(("8.8.8.8", 80))
        ip = str(s.getsockname()[0])
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class QuietThreadingTCPServer(socketserver.ThreadingTCPServer):
    """Threading TCP Server that suppresses noisy connection reset/abort errors from Sonos clients."""

    def handle_error(self, request: Any, client_address: Any) -> None:
        import sys

        exc_type, exc_value, _ = sys.exc_info()
        if exc_type is not None and issubclass(
            exc_type, (ConnectionResetError, ConnectionAbortedError)
        ):
            logger.debug(f"Connection reset/aborted by Sonos client: {exc_value}")
        else:
            super().handle_error(request, client_address)


class LocalFileServer:
    """Runs a temporary, lightweight HTTP server in a daemon thread to serve a local file to Sonos."""

    def __init__(self, filepath: str) -> None:
        self.filepath = Path(filepath).resolve()
        self.directory = self.filepath.parent
        self.filename = self.filepath.name
        self.port = 0
        self._server: QuietThreadingTCPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> str:
        """Starts the server and returns the HTTP URL accessible by Sonos."""
        # Capture current directory to prevent thread-safety problems in handler resolution
        served_dir = str(self.directory)

        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, directory=served_dir, **kwargs)

            def log_message(self, format_str: str, *args: Any) -> None:
                # Direct HTTP requests to debug log to keep stdout clean
                logger.debug(f"Local HTTP Server: {format_str % args}")

        # Bind to port 0 to let the OS automatically select a free port
        self._server = QuietThreadingTCPServer(("", 0), QuietHandler)
        self.port = self._server.server_address[1]

        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

        local_ip = get_local_ip()
        url = f"http://{local_ip}:{self.port}/{self.filename}"
        logger.info(f"Started local HTTP server at {url} serving {self.filepath}")
        return url

    def stop(self) -> None:
        """Stops the HTTP server and cleans up background threads."""
        if self._server:
            logger.info("Stopping local HTTP server...")
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None


class SonosController(AudioControllerInterface):
    """Controls a physical Sonos speaker using the soco library on the local subnet."""

    def __init__(self, speaker_name_or_ip: str, volume: int | None = None) -> None:
        self.speaker_name_or_ip = speaker_name_or_ip
        self.volume = volume
        self._device: soco.SoCo | None = None
        self._local_server: LocalFileServer | None = None

    def _get_device(self) -> soco.SoCo:
        """Retrieves and caches the soco.SoCo device.

        Attempts direct IP connection first if a valid IPv4 format is provided,
        otherwise performs automatic SSDP discovery.
        """
        if self._device is not None:
            return self._device

        # Check if the identifier is a raw IP address
        parts = self.speaker_name_or_ip.split(".")
        if len(parts) == 4 and all(p.isdigit() for p in parts):
            logger.info(
                f"Targeting Sonos IP address directly: {self.speaker_name_or_ip}"
            )
            self._device = soco.SoCo(self.speaker_name_or_ip)
            return self._device

        # Perform discovery to locate speaker by friendly name
        logger.info(
            f"Discovering Sonos devices to match name: '{self.speaker_name_or_ip}'"
        )
        discovered_devices = soco.discover()
        if discovered_devices:
            for device in discovered_devices:
                try:
                    player_name = device.player_name
                    if player_name.lower() == self.speaker_name_or_ip.lower():
                        logger.info(
                            f"Matched Sonos speaker '{player_name}' at {device.ip_address}"
                        )
                        self._device = device
                        return self._device
                except Exception as e:
                    logger.warning(
                        f"Error querying player name from discovered device: {e}"
                    )

        raise ValueError(
            f"Unable to discover or connect to Sonos speaker '{self.speaker_name_or_ip}'."
        )

    def play(self, audio_uri: str) -> None:
        """Instructs the speaker to play the specified audio URI (local file or remote URL)."""
        device = self._get_device()
        if self.volume is not None:
            logger.info(f"Setting Sonos volume to: {self.volume}%")
            try:
                device.volume = self.volume
            except Exception as e:
                logger.warning(f"Could not set Sonos volume: {e}")

        # Detect if audio_uri is a local file path
        is_local = not (
            audio_uri.startswith("http://") or audio_uri.startswith("https://")
        )
        if is_local:
            path = Path(audio_uri)
            if not path.exists():
                raise FileNotFoundError(f"Local audio file not found: {audio_uri}")

            # Stop any pre-existing server
            if self._local_server is not None:
                try:
                    self._local_server.stop()
                except Exception:
                    pass

            self._local_server = LocalFileServer(str(path))
            play_url = self._local_server.start()
        else:
            play_url = audio_uri

        logger.info(
            f"Sending play command to Sonos at {device.ip_address} for: {play_url}"
        )
        device.play_uri(play_url)

    def stop(self) -> None:
        """Sends a stop command to the speaker and shuts down any local file server."""
        device = self._get_device()
        logger.info(f"Sending stop command to Sonos at {device.ip_address}")
        try:
            device.stop()
        finally:
            if self._local_server is not None:
                try:
                    self._local_server.stop()
                except Exception as e:
                    logger.warning(f"Error shutting down local file server: {e}")
                self._local_server = None

    def get_status(self) -> str:
        """Gets current transport status (e.g. PLAYING, STOPPED, PAUSED_PLAYBACK)."""
        try:
            device = self._get_device()
            info = device.get_current_transport_info()
            state = info.get("current_transport_state", "UNKNOWN")
            return str(state) if state is not None else "UNKNOWN"
        except Exception as e:
            logger.warning(f"Could not retrieve transport status from Sonos: {e}")
            return "UNKNOWN"
