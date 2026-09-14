"""Testes do serviço OTA (sem rede / sem systemctl real)."""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from provision import ota as ota_svc


def test_needs_update_revision() -> None:
    assert ota_svc.needs_update("abc", None)
    assert ota_svc.needs_update("abc", "def")
    assert not ota_svc.needs_update("abc", "abc")
    assert not ota_svc.needs_update("", "abc")
    assert not ota_svc.needs_update("  ", None)


def test_parse_current_json_e_texto() -> None:
    assert (
        ota_svc._parse_current_body(b'{"revision":"deadbeef"}', "application/json")
        == "deadbeef"
    )
    assert (
        ota_svc._parse_current_body(b'{"version":"legacy"}', "application/json")
        == "legacy"
    )
    assert ota_svc._parse_current_body(b"abc123\n", "text/plain") == "abc123"


def test_pending_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ota_svc, "OTA_DIR", tmp_path)
    monkeypatch.setattr(ota_svc, "PENDING_PATH", tmp_path / "pending.json")
    assert ota_svc.read_pending() is None
    ota_svc.write_pending("deadbeef")
    pending = ota_svc.read_pending()
    assert pending is not None
    assert pending.revision == "deadbeef"
    ota_svc.clear_pending()
    assert ota_svc.read_pending() is None


def test_pending_legacy_version_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ota_svc, "OTA_DIR", tmp_path)
    monkeypatch.setattr(ota_svc, "PENDING_PATH", tmp_path / "pending.json")
    (tmp_path / "pending.json").write_text(
        json.dumps({"version": "old-key", "received_at": ""}), encoding="utf-8"
    )
    pending = ota_svc.read_pending()
    assert pending is not None
    assert pending.revision == "old-key"


def test_installed_revision_persist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ota_svc, "OTA_DIR", tmp_path)
    monkeypatch.setattr(
        ota_svc, "INSTALLED_REVISION_PATH", tmp_path / "installed_revision"
    )
    monkeypatch.setattr(
        ota_svc, "_LEGACY_INSTALLED_VERSION_PATH", tmp_path / "installed_version"
    )
    assert ota_svc.read_installed_revision() is None
    ota_svc.write_installed_revision("abc123")
    assert ota_svc.read_installed_revision() == "abc123"


def test_validate_ota_package_sha256(tmp_path: Path) -> None:
    inner = tmp_path / "vigia-fall-detection-linux-arm64.tar.gz"
    inner.write_bytes(b"fake-tarball-bytes")
    digest = hashlib.sha256(inner.read_bytes()).hexdigest()
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "version": "onboard",
                "sha256": digest,
                "size": inner.stat().st_size,
                "app": "vigia-fall-detection",
            }
        ),
        encoding="utf-8",
    )
    found = ota_svc.validate_ota_package(tmp_path)
    assert found == inner


def test_validate_ota_package_sha_mismatch(tmp_path: Path) -> None:
    inner = tmp_path / "vigia-fall-detection-linux-arm64.tar.gz"
    inner.write_bytes(b"x")
    (tmp_path / "manifest.json").write_text(
        json.dumps({"version": "onboard", "sha256": "0" * 64}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="sha256"):
        ota_svc.validate_ota_package(tmp_path)


def test_apply_update_rollback_on_install_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_root = tmp_path / "opt"
    bundle = install_root / "fall-detection"
    bundle.mkdir(parents=True)
    (bundle / "marker").write_text("old", encoding="utf-8")

    ota_dir = tmp_path / "ota"
    ota_dir.mkdir()
    monkeypatch.setattr(ota_svc, "OTA_DIR", ota_dir)
    monkeypatch.setattr(
        ota_svc, "INSTALLED_REVISION_PATH", ota_dir / "installed_revision"
    )
    monkeypatch.setattr(
        ota_svc, "_LEGACY_INSTALLED_VERSION_PATH", ota_dir / "installed_version"
    )
    monkeypatch.setattr(ota_svc, "PENDING_PATH", ota_dir / "pending.json")
    monkeypatch.setattr(ota_svc, "INSTALL_ROOT", install_root)
    monkeypatch.setattr(ota_svc, "BUNDLE_DIR", bundle)
    monkeypatch.setattr(ota_svc, "BUNDLE_PREV", install_root / "fall-detection.prev")
    monkeypatch.setattr(ota_svc, "stop_fall_detection", lambda: None)
    monkeypatch.setattr(ota_svc, "restart_fall_detection", lambda: None)
    monkeypatch.setattr(ota_svc, "_wait_fall_active", lambda timeout_s=30: False)

    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(ota_svc.subprocess, "run", fake_run)

    pkg_root = tmp_path / "pkg"
    pkg_root.mkdir()
    inner = pkg_root / "vigia-fall-detection-linux-arm64.tar.gz"
    inner.write_bytes(b"inner")
    digest = hashlib.sha256(inner.read_bytes()).hexdigest()
    (pkg_root / "manifest.json").write_text(
        json.dumps(
            {"version": "onboard", "sha256": digest, "size": inner.stat().st_size}
        ),
        encoding="utf-8",
    )
    (pkg_root / "install.sh").write_text("#!/bin/bash\nexit 1\n", encoding="utf-8")

    package = tmp_path / "ota.tar.gz"
    with tarfile.open(package, "w:gz") as tar:
        for name in (
            "manifest.json",
            "install.sh",
            "vigia-fall-detection-linux-arm64.tar.gz",
        ):
            tar.add(pkg_root / name, arcname=name)

    with pytest.raises(RuntimeError):
        ota_svc.apply_update(package, revision="deadbeef")

    assert (bundle / "marker").read_text(encoding="utf-8") == "old"
    assert ota_svc.read_installed_revision() is None


def test_resolve_ota_dir_usa_data_dir_em_local(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from provision import settings as settings_mod

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("VIGIA_OTA_DIR", raising=False)
    settings_mod.get_settings.cache_clear()
    assert settings_mod.resolve_ota_dir() == tmp_path / "ota"


def test_resolve_ota_dir_placa_usa_var_lib(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from provision import settings as settings_mod

    monkeypatch.setenv("DATA_DIR", "/opt/vigia")
    monkeypatch.delenv("VIGIA_OTA_DIR", raising=False)
    settings_mod.get_settings.cache_clear()
    assert settings_mod.resolve_ota_dir() == Path("/var/lib/vigia/ota")


def test_resolve_ota_dir_explicito(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from provision import settings as settings_mod

    explicit = tmp_path / "custom-ota"
    monkeypatch.setenv("DATA_DIR", "/opt/vigia")
    monkeypatch.setenv("VIGIA_OTA_DIR", str(explicit))
    settings_mod.get_settings.cache_clear()
    assert settings_mod.resolve_ota_dir() == explicit


def test_resolve_install_root_segue_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from provision import settings as settings_mod

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("VIGIA_INSTALL_ROOT", raising=False)
    settings_mod.get_settings.cache_clear()
    assert settings_mod.resolve_install_root() == tmp_path
