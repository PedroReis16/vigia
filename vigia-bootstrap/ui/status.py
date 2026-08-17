"""Snapshot de estado para o LCD."""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from provision.actions import FALL_SERVICE, fall_is_active
from provision.identity import is_provisioned
from provision.settings import get_network_path
from provision.state import get_pairing_stage, get_phase

log = logging.getLogger(__name__)

_cpu_prev: tuple[int, int, int | None] | None = None
_cpu_pct: tuple[int, int] = (0, 0)
_CGROUP_ROOT = Path("/sys/fs/cgroup")
_PROC_ROOT = Path("/proc")


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


def pids_from_cgroup_procs(text: str) -> list[int]:
    pids: list[int] = []
    for line in text.splitlines():
        raw = line.strip()
        if raw.isdigit():
            pids.append(int(raw))
    return pids


def cpu_ticks_from_stat(text: str) -> int | None:
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


def rss_kb_from_status(text: str) -> int:
    for line in text.splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return 0


def mib_from_bytes(nbytes: int) -> int:
    return max(0, min(999, int(round(nbytes / (1024.0 * 1024.0)))))


def mib_from_kb(kb: int) -> int:
    return max(0, min(999, int(round(kb / 1024.0))))


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


def _parse_systemctl_show(text: str) -> tuple[int | None, str]:
    main_pid: int | None = None
    cgroup = ""
    for line in text.splitlines():
        if line.startswith("MainPID="):
            raw = line.split("=", 1)[1].strip()
            if raw.isdigit():
                pid = int(raw)
                main_pid = pid if pid > 0 else None
        elif line.startswith("ControlGroup="):
            cgroup = line.split("=", 1)[1].strip()
    return main_pid, cgroup


def _fall_service_ids() -> tuple[int | None, str]:
    try:
        result = subprocess.run(
            ["systemctl", "show", "-p", "MainPID", "-p", "ControlGroup", FALL_SERVICE],
            capture_output=True,
            text=True,
            check=False,
            timeout=1,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, ""
    return _parse_systemctl_show(result.stdout)


def _cgroup_path(control_group: str, name: str) -> Path | None:
    if not control_group or control_group == "/":
        return None
    return _CGROUP_ROOT / control_group.lstrip("/") / name


def _cgroup_pids(control_group: str) -> list[int]:
    path = _cgroup_path(control_group, "cgroup.procs")
    if path is None:
        return []
    try:
        return pids_from_cgroup_procs(path.read_text(encoding="utf-8"))
    except OSError:
        return []


def _child_pids(pid: int) -> list[int]:
    task_dir = _PROC_ROOT / str(pid) / "task"
    children: list[int] = []
    try:
        tid_dirs = list(task_dir.iterdir())
    except OSError:
        return children
    for tid_dir in tid_dirs:
        try:
            text = (tid_dir / "children").read_text(encoding="utf-8")
        except OSError:
            continue
        for part in text.split():
            if part.isdigit():
                children.append(int(part))
    return children


def descendants_from_root(root: int) -> list[int]:
    seen: set[int] = set()
    stack = [root]
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        for child in _child_pids(pid):
            if child not in seen:
                stack.append(child)
    return list(seen)


def fall_pids(main_pid: int | None, control_group: str) -> list[int]:
    """PIDs do fall-detection: cgroup completo, senão árvore do MainPID.

    O unit é um supervisor (`multiprocessing.Process` para captura e FIWARE);
    o MainPID sozinho quase não usa CPU/RAM.
    """
    pids = _cgroup_pids(control_group)
    if pids:
        return pids
    if main_pid is None:
        return []
    return descendants_from_root(main_pid)


def _read_proc_cpu_ticks(pid: int) -> int | None:
    try:
        text = (_PROC_ROOT / str(pid) / "stat").read_text(encoding="utf-8")
    except OSError:
        return None
    return cpu_ticks_from_stat(text)


def tree_cpu_ticks(pids: list[int]) -> int | None:
    total = 0
    found = False
    for pid in pids:
        ticks = _read_proc_cpu_ticks(pid)
        if ticks is None:
            continue
        total += ticks
        found = True
    return total if found else None


def sample_cpu(pids: list[int] | None = None) -> tuple[int, int]:
    """Atualiza deltas de CPU; devolve (fall_pct, sys_pct)."""
    global _cpu_prev, _cpu_pct
    sys_sample = _read_proc_stat()
    if sys_sample is None:
        return _cpu_pct
    total, idle = sys_sample
    if pids is None:
        main_pid, cgroup = _fall_service_ids()
        pids = fall_pids(main_pid, cgroup)
    fall = tree_cpu_ticks(pids)
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
    return mib_from_kb(used)


def rss_mib_from_status(text: str) -> int:
    try:
        return mib_from_kb(rss_kb_from_status(text))
    except (IndexError, ValueError):
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


def _read_cgroup_memory_mib(control_group: str) -> int | None:
    path = _cgroup_path(control_group, "memory.current")
    if path is None:
        return None
    try:
        nbytes = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    return mib_from_bytes(nbytes)


def _sum_rss_kb(pids: list[int]) -> int:
    total = 0
    for pid in pids:
        try:
            text = (_PROC_ROOT / str(pid) / "status").read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            total += rss_kb_from_status(text)
        except (IndexError, ValueError):
            continue
    return total


def fall_rss_mib(control_group: str, pids: list[int]) -> int:
    cgroup_mib = _read_cgroup_memory_mib(control_group)
    if cgroup_mib is not None:
        return cgroup_mib
    return mib_from_kb(_sum_rss_kb(pids))


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
    main_pid, cgroup = _fall_service_ids()
    pids = fall_pids(main_pid, cgroup)
    fall_cpu, sys_cpu = sample_cpu(pids)
    return DeviceSnapshot(
        phase=get_phase(),
        pairing_stage=get_pairing_stage(),
        provisioned=is_provisioned(),
        fall_active=fall_is_active(),
        ssid=ssid,
        fall_cpu_pct=fall_cpu,
        sys_cpu_pct=sys_cpu,
        fall_rss_mib=fall_rss_mib(cgroup, pids),
        sys_used_mib=_read_sys_used_mib(),
    )
