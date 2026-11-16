"""Certificado de cliente da placa, gravado ao lado de device.json."""

from __future__ import annotations

import os
from pathlib import Path

from shared.settings import get_device_config_path


def certificate_paths(data_dir: Path | None = None) -> tuple[Path, Path]:
    directory = data_dir if data_dir is not None else get_device_config_path().parent
    return directory / "device.crt", directory / "device.key"


def store_client_certificate(
    certificate: str | None,
    private_key: str | None,
    data_dir: Path | None = None,
) -> bool:
    """Grava o par com modo restrito. Sem os dois campos, não grava nada."""
    cert_pem = (certificate or "").strip()
    key_pem = (private_key or "").strip()
    if not cert_pem or not key_pem:
        return False

    cert_path, key_path = certificate_paths(data_dir)
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    _write_private(cert_path, cert_pem)
    _write_private(key_path, key_pem)
    return True


def _write_private(path: Path, text: str) -> None:
    payload = text if text.endswith("\n") else f"{text}\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
    os.chmod(path, 0o600)
