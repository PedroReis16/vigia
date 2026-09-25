"""Testes unitários para src.bootstrap."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src import bootstrap
from src import paths


def test_venv_python_Unix():
    with patch.object(paths.sys, "platform", "darwin"):
        assert paths.venv_python(Path("/tmp/v")) == Path("/tmp/v/bin/python")


def test_venv_python_Windows():
    with patch.object(paths.sys, "platform", "win32"):
        assert paths.venv_python(Path("C:/v")) == Path("C:/v/Scripts/python.exe")


def test_ensure_venv_JaExiste_NaoRecria(tmp_path: Path):
    venv = tmp_path / ".venv"
    python = venv / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")

    with patch.object(bootstrap, "read_python_version", return_value=(3, 12)), patch.object(
        bootstrap.venv, "EnvBuilder"
    ) as builder_cls:
        result = bootstrap.ensure_venv(venv)

    assert result == python
    builder_cls.assert_not_called()


def test_ensure_venv_PythonAntigo_Recria(tmp_path: Path):
    venv = tmp_path / ".venv"
    python = venv / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")

    def _create(root: Path) -> None:
        dest = Path(root) / "bin" / "python"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("", encoding="utf-8")

    builder = MagicMock()
    builder.create.side_effect = _create

    with patch.object(bootstrap, "read_python_version", return_value=(3, 9)), patch.object(
        bootstrap.venv, "EnvBuilder", return_value=builder
    ), patch.object(bootstrap, "venv_python", return_value=python):
        result = bootstrap.ensure_venv(venv)

    builder.create.assert_called_once_with(venv)
    assert result == python


def test_resolve_host_python_AtualSuficiente():
    with patch.object(bootstrap.sys, "version_info", (3, 13, 0)):
        assert bootstrap.resolve_host_python() == Path(bootstrap.sys.executable)


def test_ensure_venv_Ausente_Cria(tmp_path: Path):
    venv = tmp_path / ".venv"

    def _create(root: Path) -> None:
        dest = Path(root) / "bin" / "python"
        dest.parent.mkdir(parents=True)
        dest.write_text("", encoding="utf-8")

    builder = MagicMock()
    builder.create.side_effect = _create

    with patch.object(bootstrap.venv, "EnvBuilder", return_value=builder), patch.object(
        bootstrap, "venv_python", return_value=venv / "bin" / "python"
    ):
        result = bootstrap.ensure_venv(venv)

    builder.create.assert_called_once_with(venv)
    assert result == venv / "bin" / "python"


def test_dependencies_are_current_StampIgual(tmp_path: Path):
    req = tmp_path / "requirements.txt"
    req.write_text("foo==1\n", encoding="utf-8")
    venv = tmp_path / ".venv"
    venv.mkdir()
    digest = bootstrap._hash_file(req)
    (venv / bootstrap._STAMP_NAME).write_text(digest + "\n", encoding="utf-8")

    assert bootstrap.dependencies_are_current(venv, req) is True


def test_dependencies_are_current_StampAusente(tmp_path: Path):
    req = tmp_path / "requirements.txt"
    req.write_text("foo==1\n", encoding="utf-8")
    venv = tmp_path / ".venv"
    venv.mkdir()

    assert bootstrap.dependencies_are_current(venv, req) is False


def test_ensure_dependencies_JaSincronizado_NaoInstala(tmp_path: Path):
    req = tmp_path / "requirements.txt"
    req.write_text("foo==1\n", encoding="utf-8")
    venv = tmp_path / ".venv"
    venv.mkdir()
    python = venv / "bin" / "python"
    python.parent.mkdir()
    python.write_text("", encoding="utf-8")
    (venv / bootstrap._STAMP_NAME).write_text(
        bootstrap._hash_file(req) + "\n", encoding="utf-8"
    )

    with patch.object(bootstrap.subprocess, "check_call") as pip:
        bootstrap.ensure_dependencies(python, req)

    pip.assert_not_called()


def test_ensure_dependencies_StampVelho_Instala(tmp_path: Path):
    req = tmp_path / "requirements.txt"
    req.write_text("foo==1\n", encoding="utf-8")
    venv = tmp_path / ".venv"
    bin_dir = venv / "bin"
    bin_dir.mkdir(parents=True)
    python = bin_dir / "python"
    python.write_text("", encoding="utf-8")

    with patch.object(bootstrap.subprocess, "check_call") as pip:
        bootstrap.ensure_dependencies(python, req)

    assert pip.call_count == 2
    assert (venv / bootstrap._STAMP_NAME).is_file()


def test_ensure_venv_scripts_on_path_PrependeScripts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    python = tmp_path / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    monkeypatch.setenv("PATH", "/usr/bin")

    bootstrap.ensure_venv_scripts_on_path(python)

    assert os.environ["PATH"].split(os.pathsep)[0] == str(python.parent)


def test_disable_ultralytics_autoinstall_DefineDefault(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("YOLO_AUTOINSTALL", raising=False)
    bootstrap.disable_ultralytics_autoinstall()
    assert os.environ["YOLO_AUTOINSTALL"] == "false"


def test_disable_ultralytics_autoinstall_RespeitaOverride(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("YOLO_AUTOINSTALL", "true")
    bootstrap.disable_ultralytics_autoinstall()
    assert os.environ["YOLO_AUTOINSTALL"] == "true"


def test_ensure_venv_scripts_on_path_NaoDuplica(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    python = tmp_path / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    scripts = str(python.parent)
    monkeypatch.setenv("PATH", f"{scripts}{os.pathsep}/usr/bin")

    bootstrap.ensure_venv_scripts_on_path(python)

    assert os.environ["PATH"].split(os.pathsep).count(scripts) == 1


def test_ensure_env_file_CopiaExample(tmp_path: Path):
    (tmp_path / ".env.example").write_text("YOLO_MODEL=yolo26s-pose\n", encoding="utf-8")
    capture = tmp_path / "capture"
    capture.mkdir()

    with patch.object(bootstrap, "onboard_root", return_value=tmp_path):
        dest = bootstrap.ensure_env_file()

    assert dest == tmp_path / ".env"
    assert dest is not None
    assert dest.read_text(encoding="utf-8") == "YOLO_MODEL=yolo26s-pose\n"


def test_ensure_env_file_JaExiste_NaoSobrescreve(tmp_path: Path):
    (tmp_path / ".env.example").write_text("NEW=1\n", encoding="utf-8")
    existing = tmp_path / ".env"
    existing.write_text("OLD=1\n", encoding="utf-8")

    with patch.object(bootstrap, "onboard_root", return_value=tmp_path):
        dest = bootstrap.ensure_env_file()

    assert dest == existing
    assert existing.read_text(encoding="utf-8") == "OLD=1\n"


def test_prepare_runtime_ForaDoVenv_Reexecuta():
    python = Path("/tmp/fake-venv/bin/python")

    with patch.object(bootstrap, "ensure_supported_interpreter"), patch.object(
        bootstrap, "ensure_env_file"
    ), patch.object(bootstrap, "ensure_venv", return_value=python), patch.object(
        bootstrap, "is_running_in_venv", return_value=False
    ), patch.object(
        bootstrap, "_reexec_in_venv", side_effect=SystemExit(0)
    ) as reexec, patch.object(bootstrap, "ensure_dependencies") as deps, patch.object(
        bootstrap, "ensure_model"
    ) as model:
        with pytest.raises(SystemExit):
            bootstrap.prepare_runtime()

    reexec.assert_called_once_with(python, "src.bootstrap")
    deps.assert_not_called()
    model.assert_not_called()


def test_main_SetupOnly_NaoExecutaCaptura():
    with patch.object(bootstrap, "prepare_runtime"), patch(
        "src.capture_runner.run_capture"
    ) as run:
        with patch.object(bootstrap.sys, "argv", ["src.bootstrap", "--setup-only"]):
            assert bootstrap.main() == 0

    run.assert_not_called()


def test_main_SemFlags_ExecutaCaptura():
    with patch.object(bootstrap, "prepare_runtime"), patch(
        "src.capture_runner.run_capture"
    ) as run:
        with patch.object(bootstrap.sys, "argv", ["src.bootstrap"]):
            assert bootstrap.main() == 0

    run.assert_called_once()


def test_prepare_runtime_NoVenv_InstalaEExporta(tmp_path: Path):
    python = tmp_path / ".venv" / "bin" / "python"

    with patch.object(bootstrap, "ensure_supported_interpreter"), patch.object(
        bootstrap, "ensure_env_file"
    ), patch.object(bootstrap, "ensure_venv", return_value=python), patch.object(
        bootstrap, "is_running_in_venv", return_value=True
    ), patch.object(
        bootstrap, "ensure_dependencies"
    ) as deps, patch.object(
        bootstrap, "ensure_model", return_value=tmp_path / "m.onnx"
    ):
        result = bootstrap.prepare_runtime(skip_model=False)

    assert result == python
    deps.assert_called_once_with(python)
