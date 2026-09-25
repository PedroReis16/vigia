"""
Inicialização do capture: venv, dependências e export YOLO.

Invocado pelo Makefile da raiz (`make capture`). Lê o `.env` central do onboard.
Usa só a stdlib até reabrir o interpretador do `.venv` deste projeto.
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

from .paths import (
    capture_root,
    is_running_in_venv,
    onboard_root,
    requirements_file,
    venv_dir,
    venv_python,
)
from .yolo_export import DEFAULT_YOLO_IMGSZ, DEFAULT_YOLO_POSE_STEM

logger = logging.getLogger(__name__)

_STAMP_NAME = ".vigia-requirements.sha256"
_BOOTSTRAP_MODULE = "src.bootstrap"
MIN_PYTHON = (3, 12)
_HOST_PYTHON_CANDIDATES = ("python3.13", "python3.12")


def _configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


def ensure_env_file() -> Path | None:
    """Garante `.env` na raiz do onboard a partir de `.env.example`."""
    example = onboard_root() / ".env.example"
    dest = onboard_root() / ".env"
    if dest.exists() or not example.is_file():
        return dest if dest.exists() else None
    shutil.copy2(example, dest)
    logger.info("Criado %s a partir de .env.example", dest)
    return dest


def _load_env() -> None:
    """Carrega o `.env` central do onboard, se python-dotenv já estiver no venv."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(onboard_root() / ".env")


def read_python_version(executable: str | Path) -> tuple[int, int] | None:
    """Lê major.minor de um interpretador; None se não for executável."""
    try:
        completed = subprocess.run(
            [
                str(executable),
                "-c",
                "import sys; print(sys.version_info[0], sys.version_info[1])",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        major_s, minor_s = completed.stdout.split()
        return int(major_s), int(minor_s)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def _python_meets_min(version: tuple[int, int] | None) -> bool:
    return version is not None and version >= MIN_PYTHON


def resolve_host_python() -> Path:
    """
    Interpretador >= 3.12 para criar o venv.

    `python3` no macOS costuma ser o 3.9 do Xcode; preferimos Homebrew.
    """
    if _python_meets_min(sys.version_info[:2]):
        return Path(sys.executable)

    names: list[str] = []
    env = (os.environ.get("HOST_PYTHON") or "").strip()
    if env:
        names.append(env)
    names.extend(_HOST_PYTHON_CANDIDATES)

    seen: set[str] = set()
    for name in names:
        found = name if Path(name).is_file() else shutil.which(name)
        if not found:
            continue
        path = Path(found)
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        if _python_meets_min(read_python_version(path)):
            return path

    need = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    current = f"{sys.version_info.major}.{sys.version_info.minor}"
    raise RuntimeError(
        f"O capture precisa de Python >= {need} (atual: {current}). "
        f"Instale python@{need} ou defina HOST_PYTHON."
    )


def ensure_supported_interpreter() -> None:
    """Reabre o bootstrap com Python >= 3.12 se o atual for mais antigo."""
    if _python_meets_min(sys.version_info[:2]):
        return
    host = resolve_host_python()
    logger.info(
        "Python %s.%s é antigo; a reabrir com %s",
        sys.version_info.major,
        sys.version_info.minor,
        host,
    )
    os.execv(str(host), [str(host), "-m", _BOOTSTRAP_MODULE, *sys.argv[1:]])


def disable_ultralytics_autoinstall() -> None:
    """
    Impede o Ultralytics de correr `pip install` no meio do export.

    As deps de export (onnx, onnxslim) vêm do requirements.txt. O AutoUpdate
    no macOS tenta coremltools e pode rebaixar o numpy do venv.
    """
    os.environ.setdefault("YOLO_AUTOINSTALL", "false")


def ensure_venv_scripts_on_path(python: Path | None = None) -> None:
    """
    Coloca o `bin/` (ou `Scripts/`) do venv no PATH.

    O Ultralytics AutoUpdate invoca `pip` direto; sem isto, o export ONNX/CoreML
    falha com "pip: command not found" mesmo usando o Python do .venv.
    """
    interpreter = python if python is not None else venv_python()
    scripts = str(interpreter.parent)
    current = os.environ.get("PATH", "")
    parts = current.split(os.pathsep) if current else []
    if scripts in parts:
        return
    os.environ["PATH"] = scripts + (os.pathsep + current if current else "")


def ensure_venv(target: Path | None = None) -> Path:
    """Cria o venv do capture se faltar (ou se o Python for < 3.12)."""
    root = target if target is not None else venv_dir()
    python = venv_python(root)
    if python.is_file():
        version = read_python_version(python)
        if _python_meets_min(version):
            return python
        label = f"{version[0]}.{version[1]}" if version else "desconhecido"
        logger.warning(
            "Venv em %s usa Python %s; a recriar com >= %s.%s.",
            root,
            label,
            MIN_PYTHON[0],
            MIN_PYTHON[1],
        )
        shutil.rmtree(root)

    logger.info(
        "Criando ambiente virtual em %s (Python %s.%s)",
        root,
        sys.version_info.major,
        sys.version_info.minor,
    )
    root.parent.mkdir(parents=True, exist_ok=True)
    builder = venv.EnvBuilder(with_pip=True, clear=False, upgrade=False)
    builder.create(root)
    if not python.is_file():
        raise RuntimeError(f"Falha ao criar o venv: {python} não existe.")
    return python


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stamp_path(venv_root: Path) -> Path:
    return venv_root / _STAMP_NAME


def dependencies_are_current(
    venv_root: Path | None = None, requirements: Path | None = None
) -> bool:
    """True se o stamp do venv coincide com o hash de requirements.txt."""
    req = requirements if requirements is not None else requirements_file()
    root = venv_root if venv_root is not None else venv_dir()
    if not req.is_file():
        return True
    stamp = _stamp_path(root)
    return stamp.is_file() and stamp.read_text(encoding="utf-8").strip() == _hash_file(
        req
    )


def _write_stamp(venv_root: Path, requirements: Path) -> None:
    _stamp_path(venv_root).write_text(_hash_file(requirements) + "\n", encoding="utf-8")


def ensure_dependencies(
    python: Path | None = None,
    requirements: Path | None = None,
    *,
    force: bool = False,
) -> None:
    """Instala `requirements.txt` no venv se ainda não estiver sincronizado."""
    req = requirements if requirements is not None else requirements_file()
    interpreter = python if python is not None else venv_python()
    venv_root = interpreter.parent.parent
    if not req.is_file():
        raise FileNotFoundError(f"requirements.txt não encontrado: {req}")
    if not force and dependencies_are_current(venv_root, req):
        logger.info("Dependências já instaladas em %s", venv_root)
        return

    logger.info("Instalando dependências de %s", req)
    subprocess.check_call(
        [str(interpreter), "-m", "pip", "install", "--upgrade", "pip"]
    )
    subprocess.check_call([str(interpreter), "-m", "pip", "install", "-r", str(req)])
    _write_stamp(venv_root, req)


def _reexec_in_venv(python: Path, module: str) -> None:
    """Substitui o processo atual pelo Python do venv."""
    argv = [str(python), "-m", module, *sys.argv[1:]]
    logger.info("Abrindo o venv (%s)", python)
    if sys.platform == "win32":
        raise SystemExit(subprocess.call(argv))
    os.execv(str(python), argv)


def ensure_model(
    model_setting: str | None = None,
    *,
    imgsz: int | None = None,
) -> Path:
    """Exporta (se preciso) o YOLO pose para a plataforma atual."""
    from .yolo_export import ensure_yolo_pose_export

    _load_env()
    stem = (model_setting or os.getenv("YOLO_MODEL") or DEFAULT_YOLO_POSE_STEM).strip()
    if imgsz is not None:
        size = max(1, int(imgsz))
    else:
        size = max(1, int(os.getenv("YOLO_IMGSZ", str(DEFAULT_YOLO_IMGSZ))))
    path = ensure_yolo_pose_export(stem, root=capture_root(), imgsz=size)
    logger.info("Modelo YOLO pronto: %s", path)
    return path


def prepare_runtime(
    *,
    reexec_module: str = _BOOTSTRAP_MODULE,
    skip_model: bool = False,
) -> Path:
    """
    Garante venv, deps e (opcionalmente) o export YOLO deste serviço.

    Se o interpretador atual não for o do venv, reabre o processo nele.
    Devolve o path do Python do venv.
    """
    _configure_logging()
    ensure_supported_interpreter()
    ensure_env_file()
    python = ensure_venv()
    ensure_venv_scripts_on_path(python)
    if not is_running_in_venv():
        _reexec_in_venv(python, reexec_module)
    ensure_venv_scripts_on_path(python)
    disable_ultralytics_autoinstall()
    ensure_dependencies(python)
    if not skip_model:
        ensure_model()
    return python


def main() -> int:
    """CLI: `make capture` → prepara o runtime e executa a captura."""
    args = sys.argv[1:]
    skip_model = "--skip-model" in args
    setup_only = "--setup-only" in args
    prepare_runtime(skip_model=skip_model)
    if setup_only:
        logger.info("Runtime do capture inicializado em %s", capture_root())
        return 0
    from .capture_runner import run_capture

    logger.info("A executar a captura em %s", capture_root())
    run_capture()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
