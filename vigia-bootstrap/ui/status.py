"""Snapshot de estado para o LCD."""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass

from provision.actions import FALL_SERVICE, fall_is_active
from provision.identity import is_provisioned
from provision.settings import get_network_path
from provision.state import get_pairing_stage, get_phase

log = logging.getLogger(__name__)

_cpu_prev: tuple[int, int, int | None] | None = None
_cpu_pct: tuple[int, int] = (0, 0)


@dataclass(frozen=True)
class DeviceSnapshot:
    phase: str
    pairing_stage: str
    provisioned: bool
    fall_active: bool
    ssid: str | None
    fall_cpu_pct: int = 0
    sys_cpu_pct: int = 0
    fall_rss_mib: int = 0
    sys_used_mib: int = 0


def percents_from_delta(
    prev_total: int,
    prev_idle: int,
    prev_fall: int | None,
    total: int,
    idle: int,
    fall: int | None,
) -> tuple[int, int]:
    dt = total - prev_total
    if dt <= 0:
        return 0, 0
    sys_pct = int(round(100.0 * (1.0 - (idle - prev_idle) / dt)))
    fall_pct = 0
    if fall is not None and prev_fall is not None:
        fall_pct = int(round(100.0 * (fall - prev_fall) / dt))
    return max(0, min(999, fall_pct)), max(0, min(999, sys_pct))


def _read_proc_stat() -> tuple[int, int] | None:
    try:
        with open("/proc/stat", encoding="utf-8") as fh:
            parts = fh.readline().split()
        values = [int(x) for x in parts[1:]]
    except (OSError, ValueError):
        return None
    if len(values) < 4:
        return None
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return sum(values), idle


def _fall_main_pid() -> int | None:
    try:
        result = subprocess.run(
            ["systemctl", "show", "-p", "MainPID", "--value", FALL_SERVICE],
            capture_output=True,
            text=True,
            check=False,
            timeout=1,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    raw = result.stdout.strip()
    if not raw.isdigit():
        return None
    pid = int(raw)
    return pid if pid > 0 else None


def _read_proc_cpu_ticks(pid: int) -> int | None:
    try:
        text = open(f"/proc/{pid}/stat", encoding="utf-8").read()
    except OSError:
        return None
    rparen = text.rfind(")")
    if rparen < 0:
        return None
    fields = text[rparen + 2 :].split()
    if len(fields) < 13:
        return None
    try:
        return int(fields[11]) + int(fields[12])
    except ValueError:
        return None


def sample_cpu() -> tuple[int, int]:
    """Atualiza deltas de CPU; devolve (fall_pct, sys_pct)."""
    global _cpu_prev, _cpu_pct
    sys_sample = _read_proc_stat()
    if sys_sample is None:
        return _cpu_pct
    total, idle = sys_sample
    pid = _fall_main_pid()
    fall = _read_proc_cpu_ticks(pid) if pid is not None else None
    prev = _cpu_prev
    _cpu_prev = (total, idle, fall)
    if prev is None:
        return _cpu_pct
    _cpu_pct = percents_from_delta(prev[0], prev[1], prev[2], total, idle, fall)
    return _cpu_pct


def reset_cpu_samples() -> None:
    global _cpu_prev, _cpu_pct
    _cpu_prev = None
    _cpu_pct = (0, 0)


def used_mib_from_meminfo(text: str) -> int:
    total_kb = 0
    avail_kb = 0
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            total_kb = int(line.split()[1])
        elif line.startswith("MemAvailable:"):
            avail_kb = int(line.split()[1])
    used = max(0, total_kb - avail_kb)
    return max(0, min(999, int(round(used / 1024.0))))


def rss_mib_from_status(text: str) -> int:
    for line in text.splitlines():
        if line.startswith("VmRSS:"):
            kb = int(line.split()[1])
            return max(0, min(999, int(round(kb / 1024.0))))
    return 0


def _read_sys_used_mib() -> int:
    try:
        text = open("/proc/meminfo", encoding="utf-8").read()
    except OSError:
        return 0
    try:
        return used_mib_from_meminfo(text)
    except (IndexError, ValueError):
        return 0


def _read_fall_rss_mib(pid: int | None) -> int:
    if pid is None:
        return 0
    try:
        text = open(f"/proc/{pid}/status", encoding="utf-8").read()
    except OSError:
        return 0
    try:
        return rss_mib_from_status(text)
    except (IndexError, ValueError):
        return 0


def _ssid_from_file() -> str | None:
    path = get_network_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        ssid = data.get("ssid")
        return str(ssid) if ssid else None
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("Falha a ler SSID: %s", exc)
        return None


def read_snapshot() -> DeviceSnapshot:
    # SSID só do ficheiro no ciclo do LCD — nmcli no loop bloqueava o I2C.
    ssid = _ssid_from_file()
    fall_cpu, sys_cpu = sample_cpu()
    pid = _fall_main_pid()
    return DeviceSnapshot(
        phase=get_phase(),
        pairing_stage=get_pairing_stage(),
        provisioned=is_provisioned(),
        fall_active=fall_is_active(),
        ssid=ssid,
        fall_cpu_pct=fall_cpu,
        sys_cpu_pct=sys_cpu,
        fall_rss_mib=_read_fall_rss_mib(pid),
        sys_used_mib=_read_sys_used_mib(),
    )
