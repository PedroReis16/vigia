"""Testes unitários para capture.main."""

from unittest.mock import patch

from capture import main


def test_main_ExecutaRunCapture() -> None:
    with patch("capture.capture_runner.run_capture") as mock_run:
        main()

    mock_run.assert_called_once_with()


def test_main_KeyboardInterrupt_NaoPropaga() -> None:
    with patch("capture.capture_runner.run_capture", side_effect=KeyboardInterrupt):
        main()
