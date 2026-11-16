"""Testes do processo pai do serviço Vigia."""

from __future__ import annotations

from types import SimpleNamespace

import main as service_main


class _Proc:
    def __init__(self, *, target, name: str, alive: bool = True) -> None:
        self.target = target
        self.name = name
        self.pid = 42
        self.alive = alive
        self.started = False

    def start(self) -> None:
        self.started = True
        self.alive = True

    def is_alive(self) -> bool:
        return self.alive

    def join(self, timeout: float | None = None) -> None:
        return None

    def terminate(self) -> None:
        self.alive = False


def test_ensure_children_arranca_os_tres_papeis() -> None:
    created: list[_Proc] = []

    def factory(*, target, name: str) -> _Proc:
        proc = _Proc(target=target, name=name)
        created.append(proc)
        return proc

    tasks: dict = {}
    service_main.ensure_children(tasks, process_factory=factory, now=10.0)

    assert [proc.name for proc in created] == [
        "vigia-capture",
        "vigia-integration",
        "vigia-interface",
    ]
    assert all(proc.started for proc in created)
    assert set(tasks) == {"capture", "integration", "interface"}


def test_ensure_children_nao_reinicia_processo_vivo() -> None:
    live = _Proc(target=lambda: None, name="vigia-capture", alive=True)
    tasks = {"capture": live}
    created: list[str] = []

    def factory(*, target, name: str) -> _Proc:
        created.append(name)
        return _Proc(target=target, name=name)

    service_main.ensure_children(
        tasks,
        process_factory=factory,
        now=10.0,
        next_start={},
    )

    assert "vigia-capture" not in created
    assert tasks["capture"] is live
    assert set(created) == {"vigia-integration", "vigia-interface"}


def test_ensure_children_espera_backoff_depois_de_terminar() -> None:
    dead = _Proc(target=lambda: None, name="vigia-capture", alive=False)
    tasks = {"capture": dead, "integration": _Proc(target=lambda: None, name="i"), "interface": _Proc(target=lambda: None, name="f")}
    created: list[str] = []
    pending: dict[str, float] = {}

    def factory(*, target, name: str) -> _Proc:
        created.append(name)
        return _Proc(target=target, name=name)

    service_main.ensure_children(
        tasks,
        now=10.0,
        next_start=pending,
        process_factory=factory,
        backoff_s=2.0,
        join_timeout=0,
    )

    assert "vigia-capture" not in created
    assert "capture" not in tasks
    assert pending["capture"] == 12.0

    service_main.ensure_children(
        tasks,
        now=12.0,
        next_start=pending,
        process_factory=factory,
        backoff_s=2.0,
        join_timeout=0,
    )

    assert "vigia-capture" in created
    assert tasks["capture"].name == "vigia-capture"
    assert "capture" not in pending


def test_stop_children_encerra_interface_integracao_e_captura(monkeypatch) -> None:
    stopped: list[str] = []

    def _stop(proc, **_kwargs) -> None:
        if proc is not None:
            stopped.append(proc.name)

    monkeypatch.setattr(service_main, "stop_child_process", _stop)
    tasks = {
        "capture": SimpleNamespace(name="capture"),
        "integration": SimpleNamespace(name="integration"),
        "interface": SimpleNamespace(name="interface"),
    }

    service_main.stop_children(tasks)

    assert stopped == ["interface", "integration", "capture"]
    assert tasks == {}
