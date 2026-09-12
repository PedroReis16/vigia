"""Export e resolução de pesos YOLO pose por plataforma (ONNX / CoreML / NCNN)."""

from __future__ import annotations

import logging
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Literal

from shared.bundle_paths import repo_or_bundle_root

logger = logging.getLogger(__name__)

YoloExportBackend = Literal["onnx", "coreml", "ncnn"]

DEFAULT_YOLO_POSE_STEM = "yolo26s-pose"
DEFAULT_YOLO_IMGSZ = 320
_YOLO_MODELS_SUBDIR = Path("models") / "yolo"


def normalize_yolo_pose_stem(model_setting: str | None) -> str:
    """Extrai o stem a partir de YOLO_POSE_MODEL (nome ou path com extensão)."""
    raw = (model_setting or "").strip() or DEFAULT_YOLO_POSE_STEM
    path = Path(raw)
    name = path.name if path.suffix else raw
    for suffix in (
        ".pt",
        ".onnx",
        ".mlpackage",
        "_ncnn_model",
        ".mlmodel",
    ):
        if name.lower().endswith(suffix):
            name = name[: -len(suffix)]
            break
    name = name.strip()
    return name or DEFAULT_YOLO_POSE_STEM


def resolve_export_imgsz(explicit: int | None = None) -> int:
    """imgsz de export/inferência: argumento, senão YOLO_IMGSZ, senão 320."""
    if explicit is not None:
        return max(1, int(explicit))
    return max(1, int(os.getenv("YOLO_IMGSZ", str(DEFAULT_YOLO_IMGSZ))))


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def detect_yolo_export_backend() -> YoloExportBackend:
    """Backend de export conforme runtime: frozen/linux→ncnn, win→onnx, mac→coreml."""
    if is_frozen():
        return "ncnn"
    if sys.platform == "win32":
        return "onnx"
    if sys.platform == "darwin":
        return "coreml"
    return "ncnn"


def yolo_export_artifact_path(
    root: Path, stem: str, backend: YoloExportBackend
) -> Path:
    """Caminho canónico do artefato exportado sob models/yolo/."""
    base = root / _YOLO_MODELS_SUBDIR
    if backend == "onnx":
        return base / f"{stem}.onnx"
    if backend == "coreml":
        return base / f"{stem}.mlpackage"
    return base / f"{stem}_ncnn_model"


def is_valid_yolo_export_artifact(path: Path, backend: YoloExportBackend) -> bool:
    """Valida presença mínima do artefato exportado."""
    if backend == "onnx":
        return path.is_file() and path.stat().st_size > 0
    if backend == "coreml":
        return path.is_dir() and any(path.iterdir())
    param = path / "model.ncnn.param"
    weights = path / "model.ncnn.bin"
    return (
        path.is_dir()
        and param.is_file()
        and param.stat().st_size > 0
        and weights.is_file()
        and weights.stat().st_size > 0
    )


def read_exported_imgsz(path: Path, backend: YoloExportBackend) -> int | None:
    """Lê o imgsz fixo do artefato exportado, se disponível."""
    try:
        if backend == "onnx":
            import onnxruntime as ort  # pyright: ignore[reportMissingImports]

            session = ort.InferenceSession(
                str(path), providers=["CPUExecutionProvider"]
            )
            shape = session.get_inputs()[0].shape
            if len(shape) >= 4:
                height, width = shape[2], shape[3]
                if isinstance(height, int) and isinstance(width, int):
                    return max(height, width)
            return None

        if backend == "ncnn":
            meta = path / "metadata.yaml"
            if not meta.is_file():
                return None
            text = meta.read_text(encoding="utf-8")
            match = re.search(
                r"imgsz:\s*(?:\n\s*-\s*(\d+)\s*\n\s*-\s*(\d+)|(\d+))",
                text,
            )
            if not match:
                return None
            if match.group(3):
                return int(match.group(3))
            return max(int(match.group(1)), int(match.group(2)))

        # CoreML: tamanho tipicamente no metadata; se indisponível, aceitar.
        return None
    except Exception as exc:  # noqa: BLE001 — metadados opcionais
        logger.debug("Não foi possível ler imgsz de %s: %s", path, exc)
        return None


def artifact_matches_imgsz(
    path: Path, backend: YoloExportBackend, imgsz: int
) -> bool:
    """True se o artefato não declara imgsz ou declara o mesmo valor."""
    actual = read_exported_imgsz(path, backend)
    if actual is None:
        return True
    return actual == imgsz


def resolve_inference_imgsz(
    model: Any, fallback: int | None = None
) -> int:
    """
    imgsz seguro para track/predict em modelos exportados com input fixo.

    Preferência: tamanho embutido no artefato (ONNX/NCNN); senão fallback/settings.
    """
    fallback_imgsz = resolve_export_imgsz(fallback)
    path_raw = getattr(model, "ckpt_path", None) or getattr(model, "model_name", None)
    if not path_raw:
        return fallback_imgsz

    path = Path(str(path_raw))
    backend: YoloExportBackend | None = None
    if path.suffix.lower() == ".onnx":
        backend = "onnx"
    elif path.is_dir() and (
        path.name.endswith("_ncnn_model") or (path / "model.ncnn.param").is_file()
    ):
        backend = "ncnn"
    elif path.suffix.lower() == ".mlpackage" or path.name.endswith(".mlpackage"):
        backend = "coreml"

    if backend is None:
        return fallback_imgsz

    actual = read_exported_imgsz(path, backend)
    return actual if actual is not None else fallback_imgsz


def _ultralytics_export_output_name(stem: str, backend: YoloExportBackend) -> str:
    if backend == "onnx":
        return f"{stem}.onnx"
    if backend == "coreml":
        return f"{stem}.mlpackage"
    return f"{stem}_ncnn_model"


def _find_export_output(
    search_roots: list[Path], stem: str, backend: YoloExportBackend
) -> Path | None:
    name = _ultralytics_export_output_name(stem, backend)
    for root in search_roots:
        candidate = root / name
        if is_valid_yolo_export_artifact(candidate, backend):
            return candidate
    return None


def _move_export_into_place(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()
    shutil.move(str(src), str(dest))
    return dest


def _remove_artifact(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()


def _run_ultralytics_export(
    stem: str, backend: YoloExportBackend, work_dir: Path, imgsz: int
) -> Path:
    from ultralytics import YOLO  # pyright: ignore[reportMissingImports]

    prev = Path.cwd()
    try:
        os.chdir(work_dir)
        model = YOLO(stem)
        exported = model.export(format=backend, imgsz=imgsz)
    finally:
        os.chdir(prev)

    if exported:
        exported_path = Path(str(exported))
        if not exported_path.is_absolute():
            exported_path = work_dir / exported_path
        if is_valid_yolo_export_artifact(exported_path, backend):
            return exported_path

    found = _find_export_output([work_dir, prev, Path.cwd()], stem, backend)
    if found is None:
        raise FileNotFoundError(
            f"Export YOLO format={backend!r} para {stem!r} não produziu artefato esperado."
        )
    return found


def _materialize_export(
    stem: str,
    backend: YoloExportBackend,
    artifact: Path,
    imgsz: int,
) -> Path:
    logger.info(
        "Exportando YOLO stem=%s format=%s imgsz=%s → %s",
        stem,
        backend,
        imgsz,
        artifact,
    )
    with tempfile.TemporaryDirectory(prefix="vigia-yolo-export-") as tmp:
        work_dir = Path(tmp)
        produced = _run_ultralytics_export(stem, backend, work_dir, imgsz)
        if produced.resolve().is_relative_to(work_dir.resolve()):
            placed = _move_export_into_place(produced, artifact)
        else:
            artifact.parent.mkdir(parents=True, exist_ok=True)
            if artifact.exists():
                _remove_artifact(artifact)
            if produced.is_dir():
                shutil.copytree(produced, artifact)
            else:
                shutil.copy2(produced, artifact)
            placed = artifact

    if not is_valid_yolo_export_artifact(placed, backend):
        raise FileNotFoundError(
            f"Falha ao materializar export YOLO em {placed} (format={backend})."
        )
    return placed.resolve()


def ensure_yolo_pose_export(
    model_setting: str | None = None,
    *,
    backend: YoloExportBackend | None = None,
    root: Path | None = None,
    imgsz: int | None = None,
) -> Path:
    """
    Garante o artefato exportado em models/yolo/ e devolve o seu path.

    - Path absoluto/existente (ficheiro ou pasta de export) → usa direto.
    - Bundle congelado → só resolve NCNN empacotado (sem export).
    - Dev → exporta via Ultralytics se o artefato ainda não existir ou o imgsz
      não coincidir com YOLO_IMGSZ (input fixo ONNX/NCNN).
    """
    raw = (model_setting or "").strip() or DEFAULT_YOLO_POSE_STEM
    candidate = Path(raw).expanduser()
    if candidate.exists() and (candidate.is_file() or candidate.is_dir()):
        return candidate.resolve()

    project_root = root if root is not None else repo_or_bundle_root()
    stem = normalize_yolo_pose_stem(raw)
    chosen = backend or detect_yolo_export_backend()
    target_imgsz = resolve_export_imgsz(imgsz)
    artifact = yolo_export_artifact_path(project_root, stem, chosen)

    if is_valid_yolo_export_artifact(artifact, chosen):
        if artifact_matches_imgsz(artifact, chosen, target_imgsz):
            return artifact.resolve()
        if is_frozen():
            logger.warning(
                "Export YOLO %s tem imgsz diferente de %s; "
                "usando artefato do bundle mesmo assim.",
                artifact,
                target_imgsz,
            )
            return artifact.resolve()
        logger.warning(
            "Export YOLO %s com imgsz incompatível (esperado %s); a reexportar.",
            artifact,
            target_imgsz,
        )
        _remove_artifact(artifact)

    if is_frozen():
        raise FileNotFoundError(
            f"Modelo YOLO {chosen} não encontrado no bundle: {artifact}. "
            "Reconstrua o instalador com ensure-model (NCNN)."
        )

    return _materialize_export(stem, chosen, artifact, target_imgsz)


def resolve_yolo_pose_weights(model_setting: str | None = None) -> str:
    """Resolve (e se necessário exporta) o path dos pesos YOLO para YOLO(...)."""
    return str(ensure_yolo_pose_export(model_setting))
