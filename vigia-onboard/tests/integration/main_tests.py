"""Testes da entrada `python -m integration`."""

from __future__ import annotations

from unittest.mock import patch

from integration import __main__ as integration_main


def test_integration_main_SetupOnly_NaoExecutaRunner():
    with patch.object(integration_main, "prepare_runtime"), patch(
        "integration.integration_runner.run_integration"
    ) as run:
        with patch.object(integration_main.sys, "argv", ["integration", "--setup-only"]):
            assert integration_main.main() == 0

    run.assert_not_called()


def test_integration_main_SemFlags_ExecutaRunner():
    with patch.object(integration_main, "prepare_runtime"), patch(
        "integration.integration_runner.run_integration"
    ) as run:
        with patch.object(integration_main.sys, "argv", ["integration"]):
            assert integration_main.main() == 0

    run.assert_called_once()


def test_integration_main_NaoPedeModelo():
    with patch.object(integration_main, "prepare_runtime") as prep, patch(
        "integration.integration_runner.run_integration"
    ):
        with patch.object(integration_main.sys, "argv", ["integration"]):
            integration_main.main()

    prep.assert_called_once_with(reexec_module="integration", skip_model=True)
