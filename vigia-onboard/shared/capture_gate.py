"""Gate em ficheiro para a captura, partilhado entre processos.

``capture.hold`` bloqueia o loop. ``capture.restart`` pede uma sessão nova
(releitura de ``classifier.json``). ``capture.pid`` indica o processo activo.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from shared.settings import get_identity_path, get_network_path, get_settings

HOLD_NAME = "capture.hold"
RESTART_NAME = "capture.restart"
PID_NAME = "capture.pid"


def _data_dir() -> Path:
    return Path(get_settings().data_dir)


def _ensure_data_dir() -> Path:
    path = _data_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def hold_path() -> Path:
    return _data_dir() / HOLD_NAME


def restart_path() -> Path:
    return _data_dir() / RESTART_NAME


def pid_path() -> Path:
    return _data_dir() / PID_NAME


def is_provisioned() -> bool:
    """True quando identity.json e network.json existem."""
    return get_identity_path().is_file() and get_network_path().is_file()


def capture_allowed() -> bool:
    """A captura só corre provisionada e sem ``capture.hold``."""
    return is_provisioned() and not hold_path().exists()


def hold_capture() -> None:
    """Impede a captura de abrir (ou manter) a sessão de câmera."""
    path = _ensure_data_dir() / HOLD_NAME
    path.write_text("hold\n", encoding="utf-8")


def release_capture() -> None:
    """Remove o hold. A captura entra quando também estiver provisionada."""
    hold_path().unlink(missing_ok=True)


def request_capture_restart() -> None:
    """Pede à captura que encerre a sessão e releia o classificador."""
    path = _ensure_data_dir() / RESTART_NAME
    path.write_text("restart\n", encoding="utf-8")


def restart_pending() -> bool:
    return restart_path().is_file()


def consume_capture_restart() -> bool:
    """Consome o pedido de restart. True se havia pedido."""
    path = restart_path()
    if not path.is_file():
        return False
    path.unlink(missing_ok=True)
    return True


def write_capture_pid(pid: int | None = None) -> None:
    """Regista o PID da sessão de captura."""
    value = os.getpid() if pid is None else int(pid)
    path = _ensure_data_dir() / PID_NAME
    path.write_text(f"{value}\n", encoding="utf-8")


def clear_capture_pid() -> None:
    pid_path().unlink(missing_ok=True)


def read_capture_pid() -> int | None:
    path = pid_path()
    if not path.is_file():
        return None
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    if pid <= 0:
        return None
    return pid


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def capture_is_active() -> bool:
    """True se o PID registado ainda é um processo vivo."""
    pid = read_capture_pid()
    if pid is None:
        return False
    return _pid_alive(pid)
