"""Testes do menu LCD sem I2C/GPIO."""

from __future__ import annotations

from ui.display import NullDisplay, fit
from ui.gpio_setup import _EventGate, _lgpio_chip_candidates
from ui.menu import CYCLE, Menu, Screen
from ui.pins import get_pin_config
from ui.status import DeviceSnapshot, percents_from_delta, reset_cpu_samples
from provision import state as pairing_state


def _snap(**kwargs) -> DeviceSnapshot:
    base = dict(
        phase="ready",
        pairing_stage=pairing_state.WAITING_APP,
        provisioned=True,
        fall_active=True,
        ssid="Casa",
        fall_cpu_pct=12,
        sys_cpu_pct=34,
    )
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


def test_navegacao_cpu_wifi_nova_rede(monkeypatch) -> None:
    snap = _snap()
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: snap)
    menu = Menu(NullDisplay())
    assert menu.screen is Screen.CPU
    menu.on_down()
    assert menu.screen is Screen.WIFI
    menu.on_ok()
    assert menu.screen is Screen.NOVA_REDE
    l1, l2 = menu.lines_for(snap)
    assert l1 == "Nova rede?"
    assert "OK" in l2


def test_ciclo_nao_inclui_unlink_nem_nova_rede() -> None:
    assert CYCLE == (Screen.CPU, Screen.WIFI, Screen.SERVICO)
    menu = Menu(NullDisplay())
    seen = []
    for _ in range(len(CYCLE)):
        seen.append(menu.screen)
        menu.on_down()
    assert seen == list(CYCLE)
    assert menu.screen is Screen.CPU


def test_wifi_mostra_ssid() -> None:
    menu = Menu(NullDisplay())
    menu.index = 1
    l1, l2 = menu.lines_for(_snap(ssid="MinhaRedeMuitoLonga"))
    assert l1 == "WiFi"
    assert l2 == "MinhaRedeMuitoLonga"
    menu.refresh(_snap(ssid="MinhaRedeMuitoLonga"))
    assert menu.last_lines[1] == "MinhaRedeMuitoLo"


def test_cpu_mostra_fall_e_sistema() -> None:
    menu = Menu(NullDisplay())
    l1, l2 = menu.lines_for(_snap(fall_cpu_pct=12, sys_cpu_pct=34))
    assert l1 == "Fall  12%"
    assert l2 == "CPU   34%"


def test_status_estagios_pareamento() -> None:
    menu = Menu(NullDisplay())
    cases = [
        (pairing_state.WAITING_APP, "Aguardando app"),
        (pairing_state.APP_CONNECTED, "App conectado"),
        (pairing_state.USER_FOUND, "Usuario encontrado"),
        (pairing_state.WAITING_WIFI, "Esperando internet"),
        (pairing_state.WIFI_CONNECTING, "A conectar..."),
        (pairing_state.WIFI_OK, "Rede OK"),
        (pairing_state.WIFI_FAIL, "Rede invalida"),
        (pairing_state.PAIRING_ERROR, "Erro vinculo"),
    ]
    for stage, expected in cases:
        snap = _snap(
            phase="pairing",
            pairing_stage=stage,
            provisioned=False,
            fall_active=False,
        )
        _, l2 = menu.lines_for(snap)
        assert l2 == expected, stage


def test_ok_nova_rede_chama_clear_wifi(monkeypatch) -> None:
    called = {"n": 0}
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())
    monkeypatch.setattr("provision.actions.clear_wifi", lambda: called.__setitem__("n", 1))
    menu = Menu(NullDisplay())
    menu.index = CYCLE.index(Screen.WIFI)
    menu.on_ok()
    menu.on_ok()
    assert called["n"] == 1
    assert menu.screen is Screen.CPU
    l1, l2 = menu.lines_for(_snap())
    assert l2 == "Rede apagada"


def test_hold_vai_desvincular(monkeypatch) -> None:
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())
    menu = Menu(NullDisplay())
    menu.on_hold()
    assert menu.screen is Screen.UNLINK
    menu.on_down()
    assert menu.screen is Screen.WIFI


def test_navegacao_durante_pairing_nao_volta_a_cpu() -> None:
    menu = Menu(NullDisplay())
    menu.index = 1
    snap = _snap(phase="pairing", provisioned=False, fall_active=False)
    menu.refresh(snap)
    assert menu.screen is Screen.WIFI


def test_refresh_iguais_nao_reescreve() -> None:
    display = NullDisplay()
    display.write_count = 0
    menu = Menu(display)
    snap = _snap()
    menu.refresh(snap)
    first = display.write_count
    menu.refresh(snap)
    assert display.write_count == first


def test_on_up_marca_dirty_e_muda_ecra() -> None:
    menu = Menu(NullDisplay())
    menu.on_up()
    assert menu.screen is Screen.SERVICO
    assert menu._dirty is True


def test_display_close_apaga() -> None:
    display = NullDisplay()
    display.write("VIGIA", "Fall parado")
    display.close()
    assert display.last == ("", "")


def test_percents_from_delta() -> None:
    fall, sys_pct = percents_from_delta(
        prev_total=1000,
        prev_idle=500,
        prev_fall=10,
        total=1100,
        idle=540,
        fall=20,
    )
    assert fall == 10
    assert sys_pct == 60


def test_percents_clamp_e_sem_fall() -> None:
    fall, sys_pct = percents_from_delta(0, 0, None, 100, 0, None)
    assert fall == 0
    assert sys_pct == 100
    fall, _ = percents_from_delta(0, 0, 0, 100, 50, 5000)
    assert fall == 999


def test_reset_cpu_samples() -> None:
    reset_cpu_samples()


def test_event_gate_ignora_duplicado() -> None:
    n = {"v": 0}
    gate = _EventGate(lockout=1.0)
    assert gate.fire("up", lambda: n.__setitem__("v", n["v"] + 1))
    assert not gate.fire("up", lambda: n.__setitem__("v", n["v"] + 1))
    assert n["v"] == 1


def test_event_gate_hold_bloqueia_ok() -> None:
    n = {"ok": 0, "hold": 0}
    gate = _EventGate()
    assert gate.fire("hold", lambda: n.__setitem__("hold", 1))
    assert not gate.fire("ok", lambda: n.__setitem__("ok", 1))
    assert n["ok"] == 0


def test_lgpio_chip_candidates(monkeypatch) -> None:
    monkeypatch.setattr("ui.gpio_setup.os.path.exists", lambda p: p == "/dev/gpiochip0")
    assert _lgpio_chip_candidates()[0] == 0
    monkeypatch.setattr("ui.gpio_setup.os.path.exists", lambda p: p == "/dev/gpiochip4")
    assert _lgpio_chip_candidates()[0] == 4
