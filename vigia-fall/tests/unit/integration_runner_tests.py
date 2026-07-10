"""Testes unitários para integration.runner."""

import pytest

from integration.runner import initialize_device_async, run_device_integration_async


class _InterrompeLoopIntegracao(Exception):
    """Exceção de controle usada apenas nos testes."""


def test_initialize_device_async_QuandoChamado_NaoLevantaExcecao(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange — nenhuma dependência externa

    # Act
    initialize_device_async()

    # Assert
    captured = capsys.readouterr()
    assert "Iniciando a integração do dispositivo" in captured.out


def test_run_device_integration_async_ComUmaIteracao_ExecutaRotina(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange
    execucoes = {"count": 0}

    def fake_sleep(_seconds: float) -> None:
        execucoes["count"] += 1
        raise _InterrompeLoopIntegracao

    monkeypatch.setattr("integration.runner.time.sleep", fake_sleep)

    # Act / Assert
    with pytest.raises(_InterrompeLoopIntegracao):
        run_device_integration_async()

    captured = capsys.readouterr()
    assert execucoes["count"] == 1
    assert "Executando a rotina de integração do dispositivo" in captured.out
