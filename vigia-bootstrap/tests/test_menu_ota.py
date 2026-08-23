"""Testes do overlay OTA no menu LCD."""

from __future__ import annotations

import asyncio

from ui.display import NullDisplay
from ui.menu import CYCLE, Menu, Screen, _progress_bar
from provision import state as pairing_state
from ui.status import DeviceSnapshot


def _snap(**kwargs) -> DeviceSnapshot:
    base = dict(
        phase="ready",
        pairing_stage=pairing_state.WAITING_APP,
        provisioned=True,
        fall_active=True,
        ssid="Casa",
        fall_cpu_pct=12,
        sys_cpu_pct=34,
        fall_rss_mib=48,
        sys_used_mib=412,
    )
    base.update(kwargs)
    return DeviceSnapshot(**base)


def test_progress_bar_16() -> None:
    assert len(_progress_bar(0)) == 16
    assert len(_progress_bar(100)) == 16
    assert "#" in _progress_bar(50)


def test_buscar_atualiz_no_ciclo() -> None:
    menu = Menu(NullDisplay())
    menu.index = CYCLE.index(Screen.ATUALIZ)
    l1, l2 = menu.lines_for(_snap())
    assert "atualiz" in l1.lower()
    assert "OK" in l2 or "procurar" in l2.lower()


def test_offer_ota_confirm_overlay(monkeypatch) -> None:
    cleared = {"n": 0}
    monkeypatch.setattr(
        "ui.menu.ota_svc.clear_pending", lambda: cleared.__setitem__("n", 1)
    )
    menu = Menu(NullDisplay())
    assert menu.offer_ota_update("1.2.3") is True
    assert menu.screen is Screen.OTA_CONFIRM
    l1, l2 = menu.lines_for(_snap())
    assert "versao" in l1.lower() or "versão" in l1.lower() or l1.startswith("Nova")
    assert l2 == ">Cancelar"
    menu.on_down()
    _, l2 = menu.lines_for(_snap())
    assert l2 == ">Confirmar"
    menu.on_up()
    menu.on_ok()
    assert cleared["n"] == 1
