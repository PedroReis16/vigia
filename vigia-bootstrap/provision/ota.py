"""OTA do fall-detection: check, download, install com rollback.

Modelo rolling (sem SemVer na API):

- ``GET {api_base_url}/devices/updates/current`` → ``{ revision, available }``
- ``GET {api_base_url}/devices/updates/download`` → pacote único sobrescrito
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

from .actions import fall_is_active, restart_fall_detection, stop_fall_detection
from .settings import get_network_path
from .sysenv import system_subprocess_env

log = logging.getLogger(__name__)

OTA_DIR = Path(os.getenv("VIGIA_OTA_DIR", "/var/lib/vigia/ota"))
PENDING_PATH = OTA_DIR / "pending.json"
INSTALLED_REVISION_PATH = OTA_DIR / "installed_revision"
# Compat: builds antigas gravavam installed_version
_LEGACY_INSTALLED_VERSION_PATH = OTA_DIR / "installed_version"

INSTALL_ROOT = Path(os.getenv("VIGIA_INSTALL_ROOT", "/opt/vigia"))
BUNDLE_DIR = INSTALL_ROOT / "fall-detection"
BUNDLE_PREV = INSTALL_ROOT / "fall-detection.prev"

INNER_TAR_NAME = "vigia-fall-detection-linux-arm64.tar.gz"
HTTP_TIMEOUT_S = 60.0
HEALTH_TIMEOUT_S = 30.0
HEALTH_POLL_S = 1.0

ProgressCb = Callable[[int], None]


@dataclass(frozen=True)
class PendingUpdate:
    revision: str
    received_at: str = ""


def ensure_ota_dir() -> Path:
    OTA_DIR.mkdir(parents=True, exist_ok=True)
    return OTA_DIR


def read_installed_revision() -> str | None:
    for path in (INSTALLED_REVISION_PATH, _LEGACY_INSTALLED_VERSION_PATH):
        if path.is_file():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text
    return None


def write_installed_revision(revision: str) -> None:
    ensure_ota_dir()
    INSTALLED_REVISION_PATH.write_text(revision.strip() + "\n", encoding="utf-8")
    try:
        _LEGACY_INSTALLED_VERSION_PATH.unlink(missing_ok=True)
    except OSError:
        pass


# Aliases usados por testes / UI antiga
read_installed_version = read_installed_revision
write_installed_version = write_installed_revision


def read_pending() -> PendingUpdate | None:
    if not PENDING_PATH.is_file():
        return None
    try:
        data = json.loads(PENDING_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("pending.json inválido: %s", exc)
        return None
    revision = str(data.get("revision") or data.get("version") or "").strip()
    if not revision:
        return None
    return PendingUpdate(
        revision=revision,
        received_at=str(data.get("received_at") or ""),
    )


def clear_pending() -> None:
    try:
        PENDING_PATH.unlink(missing_ok=True)
    except OSError as exc:
        log.warning("falha a apagar pending.json: %s", exc)


def write_pending(revision: str) -> None:
    ensure_ota_dir()
    payload = {
        "revision": revision.strip(),
        "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    PENDING_PATH.write_text(json.dumps(payload), encoding="utf-8")


def _normalize_api_base(api_base_url: str) -> str:
    return api_base_url if api_base_url.endswith("/") else f"{api_base_url}/"


def load_api_base_url() -> str:
    path = get_network_path()
    if not path.is_file():
        raise FileNotFoundError("network.json não encontrado")
    data = json.loads(path.read_text(encoding="utf-8"))
    base = str(data.get("api_base_url") or "").strip()
    if not base:
        raise ValueError("api_base_url em falta em network.json")
    return _normalize_api_base(base)


def _parse_current_body(body: bytes, content_type: str | None) -> str:
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        raise ValueError("current vazio")
    ct = (content_type or "").lower()
    if "json" in ct or text.startswith("{") or text.startswith("["):
        data = json.loads(text)
        if isinstance(data, str):
            return data.strip()
        if isinstance(data, dict):
            for key in ("revision", "version", "Revision", "Version"):
                if data.get(key):
                    return str(data[key]).strip()
        raise ValueError(f"current JSON sem revision: {text[:120]}")
    return text.splitlines()[0].strip()


def fetch_current_revision(api_base_url: str | None = None) -> str:
    base = _normalize_api_base(api_base_url or load_api_base_url())
    url = f"{base}devices/updates/current"
    req = Request(url, method="GET", headers={"Accept": "application/json"})
    with urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
        body = resp.read()
        ctype = resp.headers.get("Content-Type")
    return _parse_current_body(body, ctype)


def needs_update(remote_revision: str, installed: str | None) -> bool:
    """True se a revision remota difere da instalada (ou ainda não há instalada)."""
    remote = (remote_revision or "").strip()
    if not remote:
        return False
    if not installed:
        return True
    return remote != installed.strip()


def check_update(api_base_url: str | None = None) -> str | None:
    """Devolve a revision remota se for diferente da instalada; senão None."""
    remote = fetch_current_revision(api_base_url)
    installed = read_installed_revision()
    if needs_update(remote, installed):
        return remote
    return None


def download_update(
    dest: Path,
    *,
    api_base_url: str | None = None,
    on_progress: ProgressCb | None = None,
) -> Path:
    base = _normalize_api_base(api_base_url or load_api_base_url())
    url = f"{base}devices/updates/download"
    req = Request(url, method="GET")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            total = int(resp.headers.get("Content-Length") or 0)
            read = 0
            last_pct = -1
            with open(tmp, "wb") as out:
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    read += len(chunk)
                    if on_progress and total > 0:
                        pct = min(100, int(read * 100 / total))
                        if pct != last_pct:
                            last_pct = pct
                            on_progress(pct)
        tmp.replace(dest)
        if on_progress:
            on_progress(100)
        return dest
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(extract_dir: Path) -> dict:
    manifest_path = extract_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("manifest.json em falta no pacote OTA")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest.json inválido")
    return data


def validate_ota_package(extract_dir: Path) -> Path:
    """Valida manifest + sha256; devolve caminho do tarball interno."""
    manifest = _load_manifest(extract_dir)
    version = str(manifest.get("version") or "").strip()
    sha_expected = str(manifest.get("sha256") or "").strip().lower()
    if not version or not sha_expected:
        raise ValueError("manifest.json sem version/sha256")

    inner = extract_dir / INNER_TAR_NAME
    if not inner.is_file():
        tars = sorted(extract_dir.glob("*.tar.gz"))
        if not tars:
            raise FileNotFoundError(f"{INNER_TAR_NAME} em falta")
        inner = tars[0]

    size = manifest.get("size")
    if size is not None:
        actual_size = inner.stat().st_size
        if int(size) != actual_size:
            raise ValueError(f"size mismatch: manifest={size} file={actual_size}")

    digest = _sha256_file(inner)
    if digest != sha_expected:
        raise ValueError("sha256 do tarball não coincide com o manifest")
    return inner


def _wait_fall_active(timeout_s: float = HEALTH_TIMEOUT_S) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if fall_is_active():
            return True
        time.sleep(HEALTH_POLL_S)
    return fall_is_active()


def _backup_bundle() -> None:
    if BUNDLE_PREV.exists():
        shutil.rmtree(BUNDLE_PREV, ignore_errors=True)
    if BUNDLE_DIR.is_dir():
        shutil.copytree(BUNDLE_DIR, BUNDLE_PREV, symlinks=True)


def _restore_bundle() -> None:
    stop_fall_detection()
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR, ignore_errors=True)
    if BUNDLE_PREV.is_dir():
        shutil.move(str(BUNDLE_PREV), str(BUNDLE_DIR))
    restart_fall_detection()


def _remove_backup() -> None:
    if BUNDLE_PREV.exists():
        shutil.rmtree(BUNDLE_PREV, ignore_errors=True)


def apply_update(
    package_path: Path,
    *,
    revision: str,
    on_progress: ProgressCb | None = None,
) -> str:
    """
    Extrai pacote OTA, valida, faz backup, corre install.sh, health-check.
    Em sucesso grava installed_revision e remove .prev; em falha restaura.
    Devolve a revision instalada.
    """
    if on_progress:
        on_progress(0)

    extract_dir = Path(tempfile.mkdtemp(prefix="vigia-ota-"))
    try:
        with tarfile.open(package_path, "r:gz") as tar:
            tar.extractall(extract_dir)

        entries = list(extract_dir.iterdir())
        root = extract_dir
        if (
            len(entries) == 1
            and entries[0].is_dir()
            and not (extract_dir / "manifest.json").exists()
        ):
            root = entries[0]

        if on_progress:
            on_progress(10)

        inner_tar = validate_ota_package(root)
        install_sh = root / "install.sh"
        if not install_sh.is_file():
            raise FileNotFoundError("install.sh em falta no pacote OTA")
        os.chmod(install_sh, 0o755)

        if on_progress:
            on_progress(20)

        stop_fall_detection()
        _backup_bundle()

        if on_progress:
            on_progress(40)

        try:
            result = subprocess.run(
                ["bash", str(install_sh), str(inner_tar)],
                capture_output=True,
                text=True,
                check=False,
                env=system_subprocess_env(),
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "").strip()
                raise RuntimeError(
                    f"install.sh falhou ({result.returncode}): {detail[:400]}"
                )

            if on_progress:
                on_progress(80)

            if not _wait_fall_active():
                raise RuntimeError("health-check: fall-detection não ficou active")

            write_installed_revision(revision)
            _remove_backup()
            clear_pending()

            if on_progress:
                on_progress(100)
            log.info("OTA revision %s aplicado com sucesso", revision)
            return revision
        except Exception:
            log.exception("OTA falhou — a restaurar backup")
            _restore_bundle()
            raise
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


async def run_ota_pipeline(
    revision: str,
    *,
    on_progress: ProgressCb | None = None,
    api_base_url: str | None = None,
) -> str:
    """Download + apply (para corrotinas do menu). Bloqueante via to_thread."""
    import asyncio

    def _work() -> str:
        ensure_ota_dir()
        dest = OTA_DIR / "vigia-fall-ota-onboard.tar.gz"

        def dl_progress(pct: int) -> None:
            if on_progress:
                on_progress(min(70, int(pct * 0.7)))

        download_update(
            dest,
            api_base_url=api_base_url,
            on_progress=dl_progress,
        )

        def inst_progress(pct: int) -> None:
            if on_progress:
                on_progress(70 + int(pct * 0.3))

        try:
            return apply_update(
                dest,
                revision=revision,
                on_progress=inst_progress,
            )
        finally:
            dest.unlink(missing_ok=True)

    return await asyncio.to_thread(_work)
