"""Testes unitários para main.kill_task."""

from multiprocessing import Process
from unittest.mock import MagicMock

from main import kill_task


def test_kill_task_ComProcessoAtivo_TerminaEAguardaJoin() -> None:
    # Arrange
    processo = MagicMock(spec=Process)

    # Act
    kill_task(processo)

    # Assert
    processo.terminate.assert_called_once()
    processo.join.assert_called_once()
