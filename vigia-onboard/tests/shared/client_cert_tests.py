"""Certificado de cliente da placa."""

from __future__ import annotations

from pathlib import Path

from shared import api_tls
from shared.client_cert import store_client_certificate


def test_store_omite_quando_falta_um_lado(tmp_path: Path) -> None:
    assert store_client_certificate("cert", None, tmp_path) is False
    assert list(tmp_path.iterdir()) == []


def test_store_grava_par_restrito(tmp_path: Path) -> None:
    assert store_client_certificate("-----BEGIN CERT-----\nabc\n-----END CERT-----", "chave", tmp_path)

    cert = tmp_path / "device.crt"
    key = tmp_path / "device.key"
    assert "BEGIN CERT" in cert.read_text(encoding="utf-8")
    assert key.read_text(encoding="utf-8").strip() == "chave"
    assert cert.stat().st_mode & 0o777 == 0o600
    assert key.stat().st_mode & 0o777 == 0o600


def test_contexto_tls_so_quando_os_ficheiros_existem(tmp_path: Path, monkeypatch) -> None:
    assert api_tls.client_context(tmp_path) is None

    sentinel = object()
    monkeypatch.setattr(api_tls, "client_context", lambda data_dir=None: sentinel)
    seen: dict[str, object] = {}

    def opener(request, timeout, context=None):  # noqa: ANN001
        seen["context"] = context
        return "opened"

    monkeypatch.setattr(api_tls, "urlopen", opener)
    monkeypatch.setattr(api_tls, "get_device_config_path", lambda: tmp_path / "device.json")
    (tmp_path / "device.crt").write_text("cert", encoding="utf-8")
    (tmp_path / "device.key").write_text("key", encoding="utf-8")

    assert api_tls.open_request(object(), timeout=1) == "opened"  # type: ignore[arg-type]
    assert seen["context"] is sentinel
