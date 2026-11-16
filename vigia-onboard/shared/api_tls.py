"""Abre HTTP da API com o certificado de cliente quando o par existe."""

from __future__ import annotations

import ssl
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from shared.client_cert import certificate_paths
from shared.settings import get_device_config_path


def client_context(data_dir: Path | None = None) -> ssl.SSLContext | None:
    cert_path, key_path = certificate_paths(data_dir)
    if not cert_path.is_file() or not key_path.is_file():
        return None

    context = ssl.create_default_context()
    context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
    return context


def open_request(request: Request, timeout: float) -> Any:
    directory = get_device_config_path().parent
    context = client_context(directory)
    if context is None:
        return urlopen(request, timeout=timeout)
    return urlopen(request, timeout=timeout, context=context)
