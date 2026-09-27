"""Testes da entrada `python -m core`."""

from __future__ import annotations

from unittest.mock import patch

from core import __main__ as core_main


def test_core_main_SetupOnly_NaoExecutaRunner():
    with patch.object(core_main, "prepare_runtime"), patch(
        "core.runner.run_core"
    ) as run:
        with patch.object(core_main.sys, "argv", ["core", "--setup-only"]):
            assert core_main.main() == 0

    run.assert_not_called()


def test_core_main_SemFlags_ExecutaRunner():
    with patch.object(core_main, "prepare_runtime"), patch(
        "core.runner.run_core"
    ) as run:
        with patch.object(core_main.sys, "argv", ["core"]):
            assert core_main.main() == 0

    run.assert_called_once()


def test_core_main_NaoPedeModelo():
    with patch.object(core_main, "prepare_runtime") as prep, patch(
        "core.runner.run_core"
    ):
        with patch.object(core_main.sys, "argv", ["core"]):
            core_main.main()

    prep.assert_called_once_with(reexec_module="core", skip_model=True)
