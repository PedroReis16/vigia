"""Menu de ecrãs no LCD 16x2."""

from __future__ import annotations

import asyncio
import enum
import logging
import time

from provision import actions
from provision import ota as ota_svc
from provision import state as pairing_state
from provision.wifi import switch_network
from .display import Display, fit
from .pins import get_pin_config
from .status import DeviceSnapshot, read_snapshot

log = logging.getLogger(__name__)

FLASH_SECONDS = 2.0
HOLD_WIFI = 2.0
HOLD_UNLINK = 5.0
HOLD_EDITOR = 1.0
OTA_CONFIRM_TIMEOUT_S = 60.0
BACKSPACE = "\b"
CHARSET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    " ._-"
    + BACKSPACE
)

_STAGE_STATUS: dict[str, tuple[str, str]] = {
    pairing_state.WAITING_APP: ("VIGIA", "Aguardando app"),
    pairing_state.APP_CONNECTED: ("VIGIA", "App conectado"),
    pairing_state.USER_FOUND: ("VIGIA", "Usuario encontrado"),
    pairing_state.WAITING_WIFI: ("VIGIA", "Esperando internet"),
    pairing_state.WIFI_CONNECTING: ("WiFi", "A conectar..."),
    pairing_state.WIFI_OK: ("WiFi", "Rede OK"),
    pairing_state.WIFI_FAIL: ("WiFi", "Rede invalida"),
    pairing_state.PAIRING_ERROR: ("VIGIA", "Erro vinculo"),
}


class Screen(enum.Enum):
    CPU = 0
    WIFI = 1
    SERVICO = 2
    ATUALIZ = 3
    NOVA_REDE = 4
    UNLINK = 5
    EDIT_SSID = 6
    EDIT_PWD = 7
    WIFI_CONNECTING = 8
    OTA_CONFIRM = 9
    OTA_PROGRESS = 10
    OTA_CHECK = 11


CYCLE = (Screen.CPU, Screen.WIFI, Screen.SERVICO, Screen.ATUALIZ)


def _eff_line(prefix: str, cpu: int, mem: int, missing: bool = False) -> str:
    if missing:
        return f"{prefix} --% {mem:3d}M"
    return f"{prefix} {cpu:3d}% {mem:3d}M"


def _progress_bar(pct: int) -> str:
    pct = max(0, min(100, int(pct)))
    filled = int(round(pct * 16 / 100))
    return ("#" * filled + "-" * (16 - filled))[:16]


def _sys_line(cpu: int, mem: int, temp_c: int | None) -> str:
    """Linha do sistema: CPU + RAM; temperatura da placa quando disponível (16 cols)."""
    if temp_c is None:
        return _eff_line("S", cpu, mem)
    # "S 34%412M 55C" = 13 chars — cabe no LCD 16x2
    return f"S{cpu:3d}%{mem:3d}M{temp_c:3d}C"


class Menu:
    def __init__(self, display: Display) -> None:
        self.display = display
        self.index = 0
        self._overlay: Screen | None = None
        self.last_lines: tuple[str, str] = ("", "")
        self._flash: tuple[str, str] | None = None
        self._flash_until = 0.0
        self._dirty = True
        self._loop: asyncio.AbstractEventLoop | None = None
        self._edit_buf = ""
        self._edit_wheel = 0
        self._ssid_draft = ""
        self._pwd_draft = ""
        self._awake = True
        self._last_input = time.monotonic()
        self._standby_seconds = get_pin_config().lcd_standby_seconds
        self._choice_confirm = False
        self._ota_version: str | None = None
        self._ota_progress = 0
        self._ota_timeout_task: asyncio.Task | None = None
        self._ota_busy = False

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def _request_redraw(self) -> None:
        self.mark_dirty()
        loop = self._loop
        if loop is not None:
            loop.call_soon_threadsafe(self.refresh)

    @property
    def screen(self) -> Screen:
        if self._overlay is not None:
            return self._overlay
        return CYCLE[self.index]

    def mark_dirty(self) -> None:
        self._dirty = True

    def is_asleep(self) -> bool:
        return not self._awake

    def _busy(self) -> bool:
        return self._overlay in (
            Screen.NOVA_REDE,
            Screen.UNLINK,
            Screen.EDIT_SSID,
            Screen.EDIT_PWD,
            Screen.WIFI_CONNECTING,
            Screen.OTA_CONFIRM,
            Screen.OTA_PROGRESS,
            Screen.OTA_CHECK,
        )

    def note_input(self) -> None:
        self._last_input = time.monotonic()

    def wake(self) -> None:
        self._awake = True
        self.note_input()
        self.display.set_backlight(True)
        self.mark_dirty()
        self._request_redraw()

    def tick_standby(self) -> None:
        if self._standby_seconds <= 0 or self._busy() or not self._awake:
            return
        if time.monotonic() - self._last_input < self._standby_seconds:
            return
        self._awake = False
        self.display.set_backlight(False)

    def consume_wake(self) -> bool:
        if self._awake:
            return False
        self.wake()
        return True

    def ok_hold_seconds(self) -> float | None:
        screen = self.screen
        if screen is Screen.WIFI:
            return HOLD_WIFI
        if screen is Screen.SERVICO:
            return HOLD_UNLINK
        if screen in (Screen.EDIT_SSID, Screen.EDIT_PWD):
            return HOLD_EDITOR
        return None

    def char_repeat_enabled(self) -> bool:
        return self.screen in (Screen.EDIT_SSID, Screen.EDIT_PWD)

    def _toggle_choice(self) -> None:
        self._choice_confirm = not self._choice_confirm
        self._request_redraw()

    def _cancel_overlay(self) -> None:
        self._overlay = None
        self._choice_confirm = False
        self._request_redraw()

    def _choice_lines(self, title: str) -> tuple[str, str]:
        if self._choice_confirm:
            return title, ">Confirmar"
        return title, ">Cancelar"

    def _cancel_ota_timeout(self) -> None:
        task = self._ota_timeout_task
        self._ota_timeout_task = None
        if task is not None and not task.done():
            task.cancel()

    def offer_ota_update(self, version: str) -> bool:
        """Mostra overlay de confirmação OTA (60s). Ignora se já ocupado."""
        if self._ota_busy or self._busy():
            return False
        version = (version or "").strip()
        if not version:
            return False
        self.wake()
        self._ota_version = version
        self._choice_confirm = False
        self._overlay = Screen.OTA_CONFIRM
        self._cancel_ota_timeout()
        loop = self._loop
        if loop is not None:
            self._ota_timeout_task = loop.create_task(self._ota_confirm_timeout())
        self._request_redraw()
        return True

    async def _ota_confirm_timeout(self) -> None:
        try:
            await asyncio.sleep(OTA_CONFIRM_TIMEOUT_S)
        except asyncio.CancelledError:
            return
        if self._overlay is not Screen.OTA_CONFIRM:
            return
        log.info("OTA: timeout 60s — a ignorar pending")
        ota_svc.clear_pending()
        self._ota_version = None
        self._cancel_overlay()

    def set_ota_progress(self, pct: int) -> None:
        self._ota_progress = max(0, min(100, int(pct)))
        if self._overlay is not Screen.OTA_PROGRESS:
            self._overlay = Screen.OTA_PROGRESS
        self._request_redraw()


    def on_up(self) -> None:
        self.note_input()
        screen = self.screen
        if screen in (Screen.NOVA_REDE, Screen.UNLINK, Screen.OTA_CONFIRM):
            self._toggle_choice()
            return
        if screen in (Screen.EDIT_SSID, Screen.EDIT_PWD):
            self._edit_wheel = (self._edit_wheel - 1) % len(CHARSET)
            self._request_redraw()
            return
        if screen in (Screen.WIFI_CONNECTING, Screen.OTA_PROGRESS, Screen.OTA_CHECK):
            return
        self._overlay = None
        self.index = (self.index - 1) % len(CYCLE)
        self._request_redraw()

    def on_down(self) -> None:
        self.note_input()
        screen = self.screen
        if screen in (Screen.NOVA_REDE, Screen.UNLINK, Screen.OTA_CONFIRM):
            self._toggle_choice()
            return
        if screen in (Screen.EDIT_SSID, Screen.EDIT_PWD):
            self._edit_wheel = (self._edit_wheel + 1) % len(CHARSET)
            self._request_redraw()
            return
        if screen in (Screen.WIFI_CONNECTING, Screen.OTA_PROGRESS, Screen.OTA_CHECK):
            return
        self._overlay = None
        self.index = (self.index + 1) % len(CYCLE)
        self._request_redraw()

    def on_ok(self) -> None:
        self.note_input()
        screen = self.screen
        if screen is Screen.NOVA_REDE:
            if self._choice_confirm:
                self._start_editor(Screen.EDIT_SSID)
            else:
                self._cancel_overlay()
                return
        elif screen is Screen.EDIT_SSID:
            self._editor_commit_char()
        elif screen is Screen.EDIT_PWD:
            self._editor_commit_char()
        elif screen is Screen.UNLINK:
            if self._choice_confirm:
                log.info("LCD: desvincular utilizador")
                actions.unlink_user()
                self._set_flash("VIGIA", "Desvinculado")
                self._overlay = None
                self.index = CYCLE.index(Screen.CPU)
            else:
                self._cancel_overlay()
                return
        elif screen is Screen.OTA_CONFIRM:
            if self._choice_confirm:
                self._begin_ota_apply()
            else:
                self._cancel_ota_timeout()
                ota_svc.clear_pending()
                self._ota_version = None
                self._cancel_overlay()
                return
        elif screen is Screen.ATUALIZ:
            self._begin_ota_check()
            return
        self._request_redraw()

    def on_hold(self) -> None:
        self.note_input()
        screen = self.screen
        if screen is Screen.WIFI:
            snap = read_snapshot()
            if not snap.provisioned:
                return
            self._choice_confirm = False
            self._overlay = Screen.NOVA_REDE
        elif screen is Screen.SERVICO:
            self._choice_confirm = False
            self._overlay = Screen.UNLINK
        elif screen is Screen.EDIT_SSID:
            self._apply_pending()
            self._ssid_draft = self._edit_buf.strip()
            if not self._ssid_draft:
                self._request_redraw()
                return
            self._start_editor(Screen.EDIT_PWD)
        elif screen is Screen.EDIT_PWD:
            self._apply_pending()
            self._pwd_draft = self._edit_buf
            self._begin_wifi_switch()
        self._request_redraw()

    def _start_editor(self, overlay: Screen) -> None:
        self._overlay = overlay
        self._edit_buf = ""
        self._edit_wheel = 0

    def _editor_char(self) -> str:
        return CHARSET[self._edit_wheel]

    def _apply_pending(self) -> None:
        ch = self._editor_char()
        if ch != BACKSPACE:
            self._edit_buf += ch

    def _editor_commit_char(self) -> None:
        ch = self._editor_char()
        if ch == BACKSPACE:
            self._edit_buf = self._edit_buf[:-1]
        else:
            self._edit_buf += ch
        self._edit_wheel = 0

    def _begin_wifi_switch(self) -> None:
        self._overlay = Screen.WIFI_CONNECTING
        loop = self._loop
        if loop is None:
            log.warning("LCD: sem event loop para troca WiFi")
            self._overlay = None
            return
        ssid, password = self._ssid_draft, self._pwd_draft
        loop.create_task(self._run_wifi_switch(ssid, password))

    async def _run_wifi_switch(self, ssid: str, password: str) -> None:
        ok = await switch_network(ssid, password)
        if ok:
            self._set_flash("WiFi", "Rede OK")
        else:
            self._set_flash("WiFi", "Rede invalida")
        self._overlay = None
        self.index = CYCLE.index(Screen.WIFI)
        self.note_input()
        self._request_redraw()

    def _begin_ota_check(self) -> None:
        if self._ota_busy:
            return
        loop = self._loop
        if loop is None:
            log.warning("LCD: sem event loop para OTA check")
            return
        self._overlay = Screen.OTA_CHECK
        self._request_redraw()
        loop.create_task(self._run_ota_check())

    async def _run_ota_check(self) -> None:
        try:
            newer = await asyncio.to_thread(ota_svc.check_update)
        except Exception as exc:
            log.warning("OTA check falhou: %s", exc)
            self._set_flash("Atualizacao", "Falha check")
            self._overlay = None
            self.index = CYCLE.index(Screen.ATUALIZ)
            self.note_input()
            self._request_redraw()
            return

        if newer is None:
            self._set_flash("Atualizacao", "em dia")
            self._overlay = None
            self.index = CYCLE.index(Screen.ATUALIZ)
            self.note_input()
            self._request_redraw()
            return

        ota_svc.write_pending(newer)
        self.offer_ota_update(newer)

    def _begin_ota_apply(self) -> None:
        version = self._ota_version
        if not version or self._ota_busy:
            return
        self._cancel_ota_timeout()
        loop = self._loop
        if loop is None:
            log.warning("LCD: sem event loop para OTA apply")
            return
        self._ota_busy = True
        self._ota_progress = 0
        self._overlay = Screen.OTA_PROGRESS
        self._request_redraw()
        loop.create_task(self._run_ota_apply(version))

    async def _run_ota_apply(self, version: str) -> None:
        loop = asyncio.get_running_loop()

        def on_progress(pct: int) -> None:
            loop.call_soon_threadsafe(self.set_ota_progress, pct)

        try:
            await ota_svc.run_ota_pipeline(version, on_progress=on_progress)
            self._set_flash("Atualizacao", "OK")
        except Exception as exc:
            log.exception("OTA apply falhou: %s", exc)
            self._set_flash("Falha update", fit(str(exc))[:16].strip() or "erro")
        finally:
            self._ota_busy = False
            self._ota_version = None
            self._overlay = None
            self.index = CYCLE.index(Screen.ATUALIZ)
            self.note_input()
            self._request_redraw()

    def _set_flash(self, line1: str, line2: str) -> None:
        self._flash = (line1, line2)
        self._flash_until = time.monotonic() + FLASH_SECONDS

    def _editor_lines(self, title: str) -> tuple[str, str]:
        pending = self._editor_char()
        extra = "<-" if pending == BACKSPACE else pending
        line2 = self._edit_buf + extra
        if len(line2) > 16:
            line2 = line2[-16:]
        return title, line2

    def lines_for(self, snap: DeviceSnapshot) -> tuple[str, str]:
        if self._flash is not None and time.monotonic() < self._flash_until:
            return self._flash
        self._flash = None

        screen = self.screen
        if screen is Screen.CPU:
            pairing = snap.phase == "pairing" or (
                not snap.provisioned and snap.phase != "ready"
            )
            if pairing:
                return _STAGE_STATUS.get(
                    snap.pairing_stage, ("VIGIA", "Aguardando app")
                )
            return (
                _eff_line("F", snap.fall_cpu_pct, snap.fall_rss_mib, not snap.fall_active),
                _sys_line(snap.sys_cpu_pct, snap.sys_used_mib, snap.board_temp_c),
            )
        if screen is Screen.WIFI:
            return "WiFi", snap.ssid or "nao ligada"
        if screen is Screen.NOVA_REDE:
            return self._choice_lines("Alterar rede?")
        if screen is Screen.EDIT_SSID:
            return self._editor_lines("SSID")
        if screen is Screen.EDIT_PWD:
            return self._editor_lines("Senha")
        if screen is Screen.WIFI_CONNECTING:
            return "WiFi", "A conectar..."
        if screen is Screen.SERVICO:
            if snap.fall_active:
                return (
                    "Servico ativo",
                    _eff_line("F", snap.fall_cpu_pct, snap.fall_rss_mib),
                )
            return "Servico", "parado"
        if screen is Screen.UNLINK:
            return self._choice_lines("Desvincular?")
        if screen is Screen.ATUALIZ:
            return "Buscar atualiz.", "OK = procurar"
        if screen is Screen.OTA_CONFIRM:
            return self._choice_lines("Nova versao")
        if screen is Screen.OTA_CHECK:
            return "Atualizacao", "A procurar..."
        if screen is Screen.OTA_PROGRESS:
            return "Atualizando", _progress_bar(self._ota_progress)
        return "Desvincular?", ">Cancelar"

    def refresh(self, snapshot: DeviceSnapshot | None = None) -> None:
        if not self._awake:
            return
        snap = snapshot if snapshot is not None else read_snapshot()
        line1, line2 = self.lines_for(snap)
        fitted = (fit(line1), fit(line2))
        if fitted == self.last_lines and not self._dirty:
            return
        self._dirty = False
        self.last_lines = fitted
        self.display.write(line1, line2)
