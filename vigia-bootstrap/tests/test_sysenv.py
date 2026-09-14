"""Testes do ambiente limpo para subprocess (PyInstaller LD_LIBRARY_PATH)."""

from __future__ import annotations

from provision import sysenv


def test_system_subprocess_env_restaura_orig(monkeypatch) -> None:
    monkeypatch.setenv("LD_LIBRARY_PATH", "/opt/vigia/bootstrap/_internal:/usr/lib")
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", "/usr/lib:/lib")
    env = sysenv.system_subprocess_env()
    assert env["LD_LIBRARY_PATH"] == "/usr/lib:/lib"
    assert "LD_LIBRARY_PATH_ORIG" not in env


def test_system_subprocess_env_remove_quando_sem_orig(monkeypatch) -> None:
    monkeypatch.setenv("LD_LIBRARY_PATH", "/opt/vigia/bootstrap/_internal")
    monkeypatch.delenv("LD_LIBRARY_PATH_ORIG", raising=False)
    env = sysenv.system_subprocess_env()
    assert "LD_LIBRARY_PATH" not in env


def test_system_subprocess_env_scrub_meipass(monkeypatch) -> None:
    monkeypatch.setattr(sysenv.sys, "_MEIPASS", "/tmp/_MEIabc", raising=False)
    monkeypatch.setenv(
        "LD_LIBRARY_PATH",
        "/tmp/_MEIabc:/usr/lib",
    )
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", "/tmp/_MEIabc:/opt/other")
    env = sysenv.system_subprocess_env()
    assert env["LD_LIBRARY_PATH"] == "/opt/other"


def test_scrub_remove_marcadores_internal() -> None:
    assert (
        sysenv._scrub_path_env("/opt/app/_internal:/usr/lib:/foo/_internal/bar")
        == "/usr/lib"
    )
    assert sysenv._scrub_path_env("/opt/app/_internal") is None
