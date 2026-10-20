"""Configuração única do device em ``device.json``.

Leituras não tomam lock: ``os.replace`` entrega o documento antigo ou o novo.
O ``flock`` fica na escrita, para a interface e a integração não se apagarem.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None  # type: ignore[assignment]

from shared.settings import get_device_config_path

logger = logging.getLogger(__name__)

_LEGACY_NAMES = (
    "identity.json",
    "network.json",
    "classifier.json",
    "options.json",
    "clips.json",
    "blur.json",
)

def read_document() -> dict:
    """Lê ``device.json``. Ausente ou inválido vale ``{}``. Migra legados uma vez."""
    path = get_device_config_path()
    if not path.is_file():
        _migrate_if_needed(path)
    return _read_file(path) or {}


def section_present(name: str) -> bool:
    """True quando a secção existe. ``{}`` conta; valor ausente ou nulo não."""
    document = read_document()
    if name not in document or document[name] is None:
        return False
    if name == "classifier":
        return True
    return isinstance(document[name], dict)


def is_provisioned() -> bool:
    """True quando identity e network estão no documento."""
    return section_present("identity") and section_present("network")


def read_section(name: str):
    """Valor da secção, ou None se não existe."""
    document = read_document()
    if name not in document:
        return None
    return document[name]


def replace_section(name: str, value: object) -> None:
    """Substitui uma secção e preserva as outras."""

    def mutate(document: dict) -> None:
        document[name] = value

    update_document(mutate)


def remove_section(name: str) -> None:
    """Remove uma secção. Sem documento e sem legados, não cria ficheiro."""
    path = get_device_config_path()
    with _exclusive_lock(path.parent):
        document, imported = _load_for_update(path)
        if document is None:
            return
        document.pop(name, None)
        _atomic_write(path, document)
        if imported:
            _delete_legacy(path.parent)


def update_document(mutator: Callable[[dict], None]) -> None:
    """Aplica ``mutator`` ao documento sob lock e grava por replace."""
    path = get_device_config_path()
    with _exclusive_lock(path.parent):
        document, imported = _load_for_update(path)
        if document is None:
            document = {}
        mutator(document)
        _atomic_write(path, document)
        if imported:
            _delete_legacy(path.parent)


def _migrate_if_needed(path: Path) -> None:
    if path.is_file():
        return
    with _exclusive_lock(path.parent):
        if path.is_file():
            return
        imported = _import_legacy(path.parent)
        if imported is None:
            return
        _atomic_write(path, imported)
        _delete_legacy(path.parent)
        logger.info("device.json criado a partir dos JSON legados")


def _load_for_update(path: Path) -> tuple[dict | None, bool]:
    """Documento actual, ou o importado. ``(None, False)`` se não há nada."""
    if path.is_file():
        return _read_file(path) or {}, False
    imported = _import_legacy(path.parent)
    if imported is None:
        return None, False
    return imported, True


def _import_legacy(directory: Path) -> dict | None:
    document: dict = {}
    found = False

    identity = _legacy_dict(directory / "identity.json")
    if identity is not None:
        document["identity"] = identity
        found = True

    network = _legacy_dict(directory / "network.json")
    if network is not None:
        document["network"] = network
        found = True

    classifier_doc = _legacy_dict(directory / "classifier.json")
    if classifier_doc is not None:
        found = True
        classifier = classifier_doc.get("classifier")
        if isinstance(classifier, str):
            document["classifier"] = classifier

    options = _legacy_dict(directory / "options.json")
    if options is not None:
        document["options"] = options
        found = True
    else:
        legacy_options: dict[str, bool] = {}
        clips = _legacy_enabled(directory / "clips.json")
        blur = _legacy_enabled(directory / "blur.json")
        if clips is not None:
            legacy_options["clips"] = clips
        if blur is not None:
            legacy_options["blur"] = blur
        if legacy_options:
            document["options"] = legacy_options
            found = True
        elif (directory / "clips.json").is_file():
            found = True
        elif (directory / "blur.json").is_file():
            found = True

    if not found:
        return None
    return document


def _delete_legacy(directory: Path) -> None:
    for name in _LEGACY_NAMES:
        try:
            (directory / name).unlink(missing_ok=True)
        except OSError:
            logger.warning("falha a apagar legado %s", name)


def _legacy_dict(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _legacy_enabled(path: Path) -> bool | None:
    """None se o ficheiro não existe. False se existe e não está ligado."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    return data.get("enabled") is True


def _read_file(path: Path) -> dict | None:
    """None se o ficheiro não existe. ``{}`` se o conteúdo é inválido."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _atomic_write(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(document)
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=".device-", suffix=".json"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    os.chmod(path, 0o600)


@contextmanager
def _exclusive_lock(directory: Path) -> Iterator[None]:
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / ".device.json.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        if fcntl is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(fd)
