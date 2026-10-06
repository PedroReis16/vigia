"""Testes da entrada `python -m interface`."""

from __future__ import annotations

from unittest.mock import patch

from interface import __main__ as interface_main


def test_interface_main_SetupOnly_NaoExecutaRunner():
    with patch.object(interface_main, "prepare_runtime"), patch(
        "interface.interface_runner.run_interface"
    ) as run:
        with patch.object(interface_main.sys, "argv", ["interface", "--setup-only"]):
            assert interface_main.main() == 0

    run.assert_not_called()


def test_interface_main_SemFlags_ExecutaRunner():
    with patch.object(interface_main, "prepare_runtime"), patch(
        "interface.interface_runner.run_interface"
    ) as run:
        with patch.object(interface_main.sys, "argv", ["interface"]):
            assert interface_main.main() == 0

    run.assert_called_once()


def test_interface_main_NaoPedeModelo():
    with patch.object(interface_main, "prepare_runtime") as prep, patch(
        "interface.interface_runner.run_interface"
    ):
        with patch.object(interface_main.sys, "argv", ["interface"]):
            interface_main.main()

    prep.assert_called_once_with(reexec_module="interface", skip_model=True)
