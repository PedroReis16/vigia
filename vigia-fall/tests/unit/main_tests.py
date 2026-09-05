"""Testes unitários para main.kill_task e exigência de provisionamento."""

from multiprocessing import Process
from unittest.mock import MagicMock

import pytest

from main import _require_provisioned, kill_task


def test_kill_task_ComProcessoAtivo_TerminaEAguardaJoin() -> None:
    processo = MagicMock(spec=Process)
    processo.is_alive.return_value = True

    kill_task(processo)

    processo.terminate.assert_called_once()
    processo.join.assert_called_once_with(timeout=2.0)


def test_kill_task_None_NaoLevanta() -> None:
    kill_task(None)


def test_require_provisioned_SemFicheiros_LevantaFileNotFoundError(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    with pytest.raises(FileNotFoundError, match="não provisionado"):
        _require_provisioned()
