"""Export e resolução de pesos YOLO pose por plataforma (ONNX / CoreML / NCNN)."""

from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Literal

from shared.bundle_paths import repo_or_bundle_root

logger = logging.getLogger(__name__)

YoloExportBackend = Literal["onnx", "coreml", "ncnn"]

DEFAULT_YOLO_POSE_STEM = "yolo26s-pose"
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


def _ultralytics_export_output_name(stem: str, backend: YoloExportBackend) -> str:
    if backend == "onnx":
        return f"{stem}.onnx"
    if backend == "coreml":
        return f"{stem}.mlpackage"
    return f"{stem}_ncnn_model"


def _find_export_output(search_roots: list[Path], stem: str, backend: YoloExportBackend) -> Path | None:
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


def _run_ultralytics_export(stem: str, backend: YoloExportBackend, work_dir: Path) -> Path:
    from ultralytics import YOLO  # pyright: ignore[reportMissingImports]

    prev = Path.cwd()
    try:
        os.chdir(work_dir)
        model = YOLO(stem)
        exported = model.export(format=backend)
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


def ensure_yolo_pose_export(
    model_setting: str | None = None,
    *,
    backend: YoloExportBackend | None = None,
    root: Path | None = None,
) -> Path:
    """
    Garante o artefato exportado em models/yolo/ e devolve o seu path.

    - Path absoluto/existente (ficheiro ou pasta de export) → usa direto.
    - Bundle congelado → só resolve NCNN empacotado (sem export).
    - Dev → exporta via Ultralytics se o artefato ainda não existir.
    """
    raw = (model_setting or "").strip() or DEFAULT_YOLO_POSE_STEM
    candidate = Path(raw).expanduser()
    if candidate.exists() and (
        candidate.is_file() or candidate.is_dir()
    ):
        return candidate.resolve()

    project_root = root if root is not None else repo_or_bundle_root()
    stem = normalize_yolo_pose_stem(raw)
    chosen = backend or detect_yolo_export_backend()
    artifact = yolo_export_artifact_path(project_root, stem, chosen)

    if is_valid_yolo_export_artifact(artifact, chosen):
        return artifact.resolve()

    if is_frozen():
        raise FileNotFoundError(
            f"Modelo YOLO {chosen} não encontrado no bundle: {artifact}. "
            "Reconstrua o instalador com ensure-model (NCNN)."
        )

    logger.info(
        "Artefato YOLO ausente (%s); exportando stem=%s format=%s → %s",
        artifact,
        stem,
        chosen,
        artifact,
    )
    with tempfile.TemporaryDirectory(prefix="vigia-yolo-export-") as tmp:
        work_dir = Path(tmp)
        produced = _run_ultralytics_export(stem, chosen, work_dir)
        # Se o Ultralytics gravou fora do tmp (ex.: junto ao .pt em cache), copiar.
        if produced.resolve().is_relative_to(work_dir.resolve()):
            placed = _move_export_into_place(produced, artifact)
        else:
            artifact.parent.mkdir(parents=True, exist_ok=True)
            if artifact.exists():
                if artifact.is_dir():
                    shutil.rmtree(artifact)
                else:
                    artifact.unlink()
            if produced.is_dir():
                shutil.copytree(produced, artifact)
            else:
                shutil.copy2(produced, artifact)
            placed = artifact

    if not is_valid_yolo_export_artifact(placed, chosen):
        raise FileNotFoundError(
            f"Falha ao materializar export YOLO em {placed} (format={chosen})."
        )
    return placed.resolve()


def resolve_yolo_pose_weights(model_setting: str | None = None) -> str:
    """Resolve (e se necessário exporta) o path dos pesos YOLO para YOLO(...)."""
    return str(ensure_yolo_pose_export(model_setting))
