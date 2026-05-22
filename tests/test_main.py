# tests/test_main.py
import pytest

from base_python_project import main


def test_run(capsys: pytest.CaptureFixture[str]) -> None:
    main.run()
    captured = capsys.readouterr()
    assert captured.out == "Hello from base-python-project!\n"
