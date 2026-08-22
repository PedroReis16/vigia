"""Testes do serviço OTA (sem rede / sem systemctl real)."""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from provision import ota as ota_svc


def test_is_newer_semver() -> None:
    assert ota_svc.is_newer("1.0.1", "1.0.0")
    assert ota_svc.is_newer("2.0.0", "1.9.9")
    assert not ota_svc.is_newer("1.0.0", "1.0.0")
    assert not ota_svc.is_newer("1.0.0", "1.0.1")
    assert ota_svc.is_newer("1.0.0", None)
    assert ota_svc.is_newer("1.0.0", "1.0.0-rc.1")
    assert not ota_svc.is_newer("1.0.0-rc.1", "1.0.0")
    assert not ota_svc.is_newer("not-a-version", "1.0.0")


def test_parse_latest_json_e_texto() -> None:
    assert (
        ota_svc._parse_latest_body(b'{"version":"1.2.3"}', "application/json")
        == "1.2.3"
    )
    assert ota_svc._parse_latest_body(b"1.2.3\n", "text/plain") == "1.2.3"


def test_pending_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ota_svc, "OTA_DIR", tmp_path)
    monkeypatch.setattr(ota_svc, "PENDING_PATH", tmp_path / "pending.json")
    assert ota_svc.read_pending() is None
    ota_svc.write_pending("9.8.7")
    pending = ota_svc.read_pending()
    assert pending is not None
    assert pending.version == "9.8.7"
    ota_svc.clear_pending()
    assert ota_svc.read_pending() is None


def test_installed_version_persist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ota_svc, "OTA_DIR", tmp_path)
    monkeypatch.setattr(ota_svc, "INSTALLED_VERSION_PATH", tmp_path / "installed_version")
    assert ota_svc.read_installed_version() is None
    ota_svc.write_installed_version("3.2.1")
    assert ota_svc.read_installed_version() == "3.2.1"


def test_validate_ota_package_sha256(tmp_path: Path) -> None:
    inner = tmp_path / "vigia-fall-detection-linux-arm64.tar.gz"
    inner.write_bytes(b"fake-tarball-bytes")
    digest = hashlib.sha256(inner.read_bytes()).hexdigest()
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "sha256": digest,
                "size": inner.stat().st_size,
                "app": "vigia-fall-detection",
            }
        ),
        encoding="utf-8",
    )
    found = ota_svc.validate_ota_package(tmp_path, expected_version="1.0.0")
    assert found == inner


def test_validate_ota_package_sha_mismatch(tmp_path: Path) -> None:
    inner = tmp_path / "vigia-fall-detection-linux-arm64.tar.gz"
    inner.write_bytes(b"x")
    (tmp_path / "manifest.json").write_text(
        json.dumps({"version": "1.0.0", "sha256": "0" * 64}),
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
    monkeypatch.setattr(ota_svc, "INSTALLED_VERSION_PATH", ota_dir / "installed_version")
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
        json.dumps({"version": "2.0.0", "sha256": digest, "size": inner.stat().st_size}),
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
        ota_svc.apply_update(package, expected_version="2.0.0")

    assert (bundle / "marker").read_text(encoding="utf-8") == "old"
    assert ota_svc.read_installed_version() is None
