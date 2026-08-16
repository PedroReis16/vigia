"""Testes do menu LCD sem I2C/GPIO."""

from __future__ import annotations

import asyncio
import json

from ui.display import NullDisplay, fit
from ui.gpio_setup import ButtonPoller, _EventGate, _lgpio_chip_candidates
from ui.menu import BACKSPACE, CHARSET, CYCLE, HOLD_UNLINK, HOLD_WIFI, Menu, Screen
from ui.pins import get_pin_config
from ui.status import (
    DeviceSnapshot,
    percents_from_delta,
    reset_cpu_samples,
    rss_mib_from_status,
    used_mib_from_meminfo,
)
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
        fall_rss_mib=48,
        sys_used_mib=412,
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


def test_lcd_standby_seconds_env(monkeypatch) -> None:
    monkeypatch.setenv("LCD_STANDBY_SECONDS", "15")
    get_pin_config.cache_clear()
    assert get_pin_config().lcd_standby_seconds == 15.0
    get_pin_config.cache_clear()


def test_navegacao_wifi_hold_alterar_rede(monkeypatch) -> None:
    snap = _snap()
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: snap)
    menu = Menu(NullDisplay())
    assert menu.screen is Screen.CPU
    menu.on_down()
    assert menu.screen is Screen.WIFI
    assert menu.ok_hold_seconds() == HOLD_WIFI
    menu.on_hold()
    assert menu.screen is Screen.NOVA_REDE
    l1, l2 = menu.lines_for(snap)
    assert l1 == "Alterar rede?"
    assert l2 == ">Cancelar"
    menu.on_down()
    assert menu.screen is Screen.NOVA_REDE
    assert menu.index == CYCLE.index(Screen.WIFI)
    _, l2 = menu.lines_for(snap)
    assert l2 == ">Confirmar"
    menu.on_ok()
    assert menu.screen is Screen.EDIT_SSID


def test_ciclo_nao_inclui_overlays() -> None:
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
    l1, l2 = menu.lines_for(_snap(fall_cpu_pct=12, sys_cpu_pct=34, fall_rss_mib=48, sys_used_mib=412))
    assert l1 == "F  12%  48M"
    assert l2 == "S  34% 412M"


def test_cpu_fall_parado() -> None:
    menu = Menu(NullDisplay())
    l1, _ = menu.lines_for(_snap(fall_active=False, fall_rss_mib=0))
    assert l1 == "F --%   0M"


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


def test_ok_servico_nao_reinicia(monkeypatch) -> None:
    called = {"n": 0}
    monkeypatch.setattr(
        "provision.actions.restart_fall_detection",
        lambda: called.__setitem__("n", 1),
    )
    menu = Menu(NullDisplay())
    menu.index = CYCLE.index(Screen.SERVICO)
    menu.on_ok()
    assert called["n"] == 0
    assert menu.screen is Screen.SERVICO


def test_hold_servico_desvincular(monkeypatch) -> None:
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())
    menu = Menu(NullDisplay())
    menu.index = CYCLE.index(Screen.SERVICO)
    assert menu.ok_hold_seconds() == HOLD_UNLINK
    menu.on_hold()
    assert menu.screen is Screen.UNLINK
    _, l2 = menu.lines_for(_snap())
    assert l2 == ">Cancelar"
    menu.on_down()
    assert menu.screen is Screen.UNLINK
    assert menu.index == CYCLE.index(Screen.SERVICO)
    _, l2 = menu.lines_for(_snap())
    assert l2 == ">Confirmar"
    menu.on_up()
    menu.on_ok()
    assert menu.screen is Screen.SERVICO


def test_ok_cancelar_nao_entra_editor(monkeypatch) -> None:
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())
    menu = Menu(NullDisplay())
    menu.index = CYCLE.index(Screen.WIFI)
    menu.on_hold()
    menu.on_ok()
    assert menu.screen is Screen.WIFI


def test_confirmar_desvincular(monkeypatch) -> None:
    called = {"n": 0}
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())
    monkeypatch.setattr("provision.actions.unlink_user", lambda: called.__setitem__("n", 1))
    menu = Menu(NullDisplay())
    menu.index = CYCLE.index(Screen.SERVICO)
    menu.on_hold()
    menu.on_down()
    menu.on_ok()
    assert called["n"] == 1
    assert menu.screen is Screen.CPU
    menu = Menu(NullDisplay())
    assert menu.ok_hold_seconds() is None
    menu.on_hold()
    assert menu.screen is Screen.CPU


def test_editor_ssid_append_ciclo_e_backspace(monkeypatch) -> None:
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())
    menu = Menu(NullDisplay())
    menu.index = CYCLE.index(Screen.WIFI)
    menu.on_hold()
    menu.on_down()
    menu.on_ok()
    assert menu.screen is Screen.EDIT_SSID
    menu.on_ok()
    assert menu._edit_buf == "A"
    menu.on_down()
    menu.on_ok()
    assert menu._edit_buf == "AB"
    menu._edit_wheel = CHARSET.index(BACKSPACE)
    menu.on_ok()
    assert menu._edit_buf == "A"
    _, line2 = menu.lines_for(_snap())
    assert "A" in line2


def test_senha_visivel(monkeypatch) -> None:
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())
    menu = Menu(NullDisplay())
    menu._overlay = Screen.EDIT_PWD
    menu._edit_buf = "segredo"
    menu._edit_wheel = 0
    l1, l2 = menu.lines_for(_snap())
    assert l1 == "Senha"
    assert l2.startswith("segredo")
    assert "*" not in l2


def test_wifi_switch_sucesso(monkeypatch) -> None:
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())
    called = {"ssid": None}

    async def fake_switch(ssid, password):
        called["ssid"] = ssid
        return True

    monkeypatch.setattr("ui.menu.switch_network", fake_switch)
    menu = Menu(NullDisplay())
    menu._ssid_draft = "Nova"
    menu._pwd_draft = "x"
    asyncio.run(menu._run_wifi_switch("Nova", "x"))
    assert called["ssid"] == "Nova"
    l1, l2 = menu.lines_for(_snap())
    assert l2 == "Rede OK"


def test_wifi_switch_falha_nao_muda_ecra_ciclo(monkeypatch) -> None:
    monkeypatch.setattr("ui.menu.read_snapshot", lambda: _snap())

    async def fake_switch(ssid, password):
        return False

    monkeypatch.setattr("ui.menu.switch_network", fake_switch)
    menu = Menu(NullDisplay())
    asyncio.run(menu._run_wifi_switch("Bad", "x"))
    assert menu.screen is Screen.WIFI
    _, l2 = menu.lines_for(_snap())
    assert l2 == "Rede invalida"


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


def test_standby_primeiro_clique_nao_navega() -> None:
    display = NullDisplay()
    menu = Menu(display)
    menu._standby_seconds = 0.01
    menu._last_input = 0.0
    menu.tick_standby()
    assert menu.is_asleep()
    assert display.backlight is False
    index = menu.index
    assert menu.consume_wake() is True
    assert menu.is_asleep() is False
    assert display.backlight is True
    assert menu.index == index
    menu.on_down()
    assert menu.screen is Screen.WIFI


def test_refresh_nao_escreve_em_standby() -> None:
    display = NullDisplay()
    menu = Menu(display)
    menu.refresh(_snap())
    count = display.write_count
    menu._awake = False
    menu.refresh(_snap(sys_cpu_pct=99))
    assert display.write_count == count


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


def test_meminfo_e_rss() -> None:
    mem = used_mib_from_meminfo("MemTotal: 1024000 kB\nMemAvailable: 512000 kB\n")
    assert mem == 500
    assert rss_mib_from_status("VmRSS:\t49152 kB\n") == 48


def test_reset_cpu_samples() -> None:
    reset_cpu_samples()


def test_event_gate_ignora_duplicado() -> None:
    n = {"v": 0}
    gate = _EventGate(lockout=1.0)
    assert gate.fire("up", lambda: n.__setitem__("v", n["v"] + 1))
    assert not gate.fire("up", lambda: n.__setitem__("v", n["v"] + 1))
    assert n["v"] == 1


def test_event_gate_hold_nao_bloqueia_ok() -> None:
    n = {"ok": 0, "hold": 0}
    gate = _EventGate()
    assert gate.fire("hold", lambda: n.__setitem__("hold", 1))
    assert gate.fire("ok", lambda: n.__setitem__("ok", 1))
    assert n["ok"] == 1


class _FakeBtn:
    def __init__(self) -> None:
        self.is_pressed = False


def test_editor_segura_desce_repete_caracteres(monkeypatch) -> None:
    clock = {"t": 1000.0}
    monkeypatch.setattr("ui.gpio_setup.time.monotonic", lambda: clock["t"])
    menu = Menu(NullDisplay())
    menu._overlay = Screen.EDIT_SSID
    assert menu.char_repeat_enabled()
    btn_ok, btn_up, btn_down = _FakeBtn(), _FakeBtn(), _FakeBtn()
    poller = ButtonPoller(btn_ok, btn_up, btn_down, _EventGate(lockout=0.0))
    btn_down.is_pressed = True
    poller.poll(menu)
    first = menu._edit_wheel
    clock["t"] += 0.2
    poller.poll(menu)
    assert menu._edit_wheel == first
    clock["t"] += 0.2
    poller.poll(menu)
    assert menu._edit_wheel == (first + 1) % len(CHARSET)
    clock["t"] += ButtonPoller.REPEAT_INTERVAL
    poller.poll(menu)
    assert menu._edit_wheel == (first + 2) % len(CHARSET)


def test_ciclo_segura_nao_repete_ecra(monkeypatch) -> None:
    clock = {"t": 1000.0}
    monkeypatch.setattr("ui.gpio_setup.time.monotonic", lambda: clock["t"])
    menu = Menu(NullDisplay())
    btn_ok, btn_up, btn_down = _FakeBtn(), _FakeBtn(), _FakeBtn()
    poller = ButtonPoller(btn_ok, btn_up, btn_down, _EventGate(lockout=0.0))
    btn_down.is_pressed = True
    poller.poll(menu)
    assert menu.screen is Screen.WIFI
    clock["t"] += 1.0
    poller.poll(menu)
    assert menu.screen is Screen.WIFI


def test_lgpio_chip_candidates(monkeypatch) -> None:
    monkeypatch.setattr("ui.gpio_setup.os.path.exists", lambda p: p == "/dev/gpiochip0")
    assert _lgpio_chip_candidates()[0] == 0
    monkeypatch.setattr("ui.gpio_setup.os.path.exists", lambda p: p == "/dev/gpiochip4")
    assert _lgpio_chip_candidates()[0] == 4
