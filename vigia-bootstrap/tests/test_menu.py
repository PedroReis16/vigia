"""Testes do menu LCD sem I2C/GPIO."""

from __future__ import annotations

from ui.display import NullDisplay, fit
from ui.menu import Menu, Screen
from ui.pins import get_pin_config
from ui.status import DeviceSnapshot


def _snap(**kwargs) -> DeviceSnapshot:
    base = dict(phase="ready", provisioned=True, fall_active=True, ssid="Casa")
    base.update(kwargs)
    return DeviceSnapshot(**base)


def test_fit_trunca_e_preenche_16() -> None:
    assert len(fit("abcdefghijklmnopqrstuvwxyz")) == 16
    assert fit("abc") == "abc" + " " * 13
    assert "a" in fit("ação")


def test_lcd_enabled_false(monkeypatch) -> None:
    monkeypatch.setenv("LCD_ENABLED", "false")
    get_pin_config.cache_clear()
    assert get_pin_config().lcd_enabled is False
    get_pin_config.cache_clear()


def test_navegacao_status_wifi_nova_rede(monkeypatch) -> None:
    snap = _snap()
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: snap)
    menu = Menu(NullDisplay())
    assert menu.screen is Screen.STATUS
    menu.on_down()
    assert menu.screen is Screen.WIFI
    menu.on_ok()
    assert menu.screen is Screen.NOVA_REDE
    l1, l2 = menu.lines_for(snap)
    assert l1 == "Nova rede?"
    assert "OK" in l2


def test_wifi_mostra_ssid() -> None:
    menu = Menu(NullDisplay())
    menu.index = 1
    l1, l2 = menu.lines_for(_snap(ssid="MinhaRedeMuitoLonga"))
    assert l1 == "WiFi"
    assert l2 == "MinhaRedeMuitoLonga"
    menu.refresh(_snap(ssid="MinhaRedeMuitoLonga"))
    assert menu.last_lines[1] == "MinhaRedeMuitoLo"


def test_status_pareando() -> None:
    menu = Menu(NullDisplay())
    _, l2 = menu.lines_for(_snap(phase="pairing", provisioned=False, fall_active=False))
    assert l2 == "Pareando user"


def test_ok_nova_rede_chama_clear_wifi(monkeypatch) -> None:
    called = {"n": 0}
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())
    monkeypatch.setattr("provision.actions.clear_wifi", lambda: called.__setitem__("n", 1))
    menu = Menu(NullDisplay())
    menu.index = 2
    menu.on_ok()
    assert called["n"] == 1
    assert menu.screen is Screen.STATUS


def test_hold_vai_desvincular(monkeypatch) -> None:
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())
    menu = Menu(NullDisplay())
    menu.on_hold()
    assert menu.screen is Screen.UNLINK


def test_pairing_snapback_para_status(monkeypatch) -> None:
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap(phase="pairing"))
    menu = Menu(NullDisplay())
    menu.index = 1
    menu._last_nav = 0.0
    menu.refresh(_snap(phase="pairing"))
    assert menu.screen is Screen.STATUS
