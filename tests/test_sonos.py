from unittest.mock import MagicMock, patch

from smart_alarm.sonos import SonosController


@patch("soco.discover")
@patch("soco.SoCo")
def test_sonos_controller_volume(mock_soco: MagicMock, mock_discover: MagicMock) -> None:
    # Test when volume is set
    controller = SonosController("192.168.0.100", volume=45)

    mock_device = MagicMock()
    mock_soco.return_value = mock_device

    controller.play("http://test-audio.mp3")

    mock_soco.assert_called_with("192.168.0.100")
    assert mock_device.volume == 45
    mock_device.play_uri.assert_called_with("http://test-audio.mp3")


@patch("soco.discover")
@patch("soco.SoCo")
def test_sonos_controller_no_volume(
    mock_soco: MagicMock, mock_discover: MagicMock
) -> None:
    # Test when volume is None
    controller = SonosController("192.168.0.100", volume=None)

    mock_device = MagicMock()
    mock_soco.return_value = mock_device

    controller.play("http://test-audio.mp3")

    # Assert volume is not set on mock device
    assert not mock_device.volume.called


@patch("soco.discover")
@patch("soco.SoCo")
@patch("smart_alarm.sonos.Path.exists")
@patch("smart_alarm.sonos.LocalFileServer")
def test_sonos_controller_local_file(
    mock_server_class: MagicMock,
    mock_exists: MagicMock,
    mock_soco: MagicMock,
    mock_discover: MagicMock,
) -> None:
    mock_exists.return_value = True

    mock_server = MagicMock()
    mock_server.start.return_value = "http://192.168.0.150:8000/alarm.mp3"
    mock_server_class.return_value = mock_server

    mock_device = MagicMock()
    mock_soco.return_value = mock_device

    controller = SonosController("192.168.0.100")
    controller.play("C:/music/alarm.mp3")

    # LocalFileServer is called with resolved local path string
    mock_server_class.assert_called_once()
    mock_server.start.assert_called_once()
    mock_device.play_uri.assert_called_with("http://192.168.0.150:8000/alarm.mp3")

    controller.stop()
    mock_server.stop.assert_called_once()


def test_local_file_server_lifecycle() -> None:
    import tempfile
    import urllib.request
    from pathlib import Path

    from smart_alarm.sonos import LocalFileServer

    # Create a temporary file to serve
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(b"mock mp3 data")
        tmp_name = tmp.name

    try:
        server = LocalFileServer(tmp_name)
        url = server.start()

        # Verify the URL format is correct
        assert url.startswith("http://")
        assert url.endswith(Path(tmp_name).name)

        # Test fetching the file
        with urllib.request.urlopen(url) as response:
            data = response.read()
            assert data == b"mock mp3 data"

        server.stop()
    finally:
        import os

        try:
            os.unlink(tmp_name)
        except Exception:
            pass


@patch("smart_alarm.sonos.logger")
def test_quiet_threading_tcp_server_suppression(mock_logger: MagicMock) -> None:
    import socketserver

    from smart_alarm.sonos import QuietThreadingTCPServer

    class DummyHandler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            pass

    server = QuietThreadingTCPServer(("", 0), DummyHandler)
    try:
        # Patch sys.exc_info to return ConnectionResetError
        with patch("sys.exc_info") as mock_exc_info:
            mock_exc_info.return_value = (
                ConnectionResetError,
                ConnectionResetError("Connection reset by peer"),
                None,
            )
            # Call handle_error
            # It should log a debug message and not call super().handle_error
            with patch(
                "socketserver.ThreadingTCPServer.handle_error"
            ) as mock_super_handle:
                server.handle_error(MagicMock(), MagicMock())
                mock_super_handle.assert_not_called()
                mock_logger.debug.assert_called_once()

        # Now test other errors that should NOT be suppressed
        with patch("sys.exc_info") as mock_exc_info_other:
            mock_exc_info_other.return_value = (
                ValueError,
                ValueError("Some other error"),
                None,
            )
            with patch(
                "socketserver.ThreadingTCPServer.handle_error"
            ) as mock_super_handle:
                server.handle_error(MagicMock(), MagicMock())
                mock_super_handle.assert_called_once()
    finally:
        server.server_close()

