"""Testes da entrada `python -m capture`."""

from __future__ import annotations

from unittest.mock import patch

from capture import __main__ as capture_main


def test_capture_main_SetupOnly_NaoExecutaCaptura():
    with patch.object(capture_main, "prepare_runtime"), patch(
        "capture.capture_runner.run_capture"
    ) as run:
        with patch.object(capture_main.sys, "argv", ["capture", "--setup-only"]):
            assert capture_main.main() == 0

    run.assert_not_called()


def test_capture_main_SemFlags_ExecutaCaptura():
    with patch.object(capture_main, "prepare_runtime"), patch(
        "capture.capture_runner.run_capture"
    ) as run:
        with patch.object(capture_main.sys, "argv", ["capture"]):
            assert capture_main.main() == 0

    run.assert_called_once()


def test_capture_main_PedeModelo():
    with patch.object(capture_main, "prepare_runtime") as prep, patch(
        "capture.capture_runner.run_capture"
    ):
        with patch.object(capture_main.sys, "argv", ["capture"]):
            capture_main.main()

    prep.assert_called_once_with(reexec_module="capture", skip_model=False)
