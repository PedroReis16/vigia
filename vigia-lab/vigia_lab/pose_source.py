"""Fonte de frames: o MESMO `model.track(source, stream=True, **kwargs)` do vigia.

Os kwargs são lidos por AST do `capture_runner.py` do onboard (fonte única da
verdade, sem importar o módulo que puxa gate/SHM/stream). Se o Pedro renomear
a constante, o lab falha alto em vez de rodar com parâmetros diferentes.
"""

from __future__ import annotations

import ast
import time
from pathlib import Path
from typing import Any, Iterator

from vigia_lab import bootstrap
from vigia_lab.session import PoseFrame

_CONST_NAME = "_YOLO_STREAM_KWARGS"


def read_stream_kwargs(runner_path: Path | None = None) -> dict[str, Any]:
    path = runner_path or bootstrap.ONBOARD_ROOT / "capture" / "capture_runner.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        target = getattr(node, "target", None) or (node.targets[0] if isinstance(node, ast.Assign) else None)
        if getattr(target, "id", None) == _CONST_NAME:
            return ast.literal_eval(node.value)
    raise RuntimeError(f"{_CONST_NAME} não encontrado em {path}; o onboard mudou?")


def stream_calls_model_track_with_kwargs(runner_path: Path | None = None) -> bool:
    """Garante que `_stream_results` continua sendo `model.track(source, **KWARGS)`."""
    path = runner_path or bootstrap.ONBOARD_ROOT / "capture" / "capture_runner.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_stream_results":
            src = ast.unparse(node.body[-1]) if node.body else ""
            return src == f"return model.track(source, **{_CONST_NAME})"
    return False


def native_fps(source: int | str) -> float | None:
    """FPS reportado pelo driver/arquivo. Abre e libera (como o capture_runner)
    ANTES do `track`, para não haver duas aberturas simultâneas da câmera."""
    import cv2

    cap = cv2.VideoCapture(source)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
    finally:
        cap.release()
    return float(fps) if fps and fps > 0 else None


def close_stream(model: Any) -> None:
    """Para as threads de leitura e libera a câmera do Ultralytics.

    Fechar o gerador do `track` (ou dar `break`) NÃO fecha o `LoadStreams`: a thread
    continua lendo a câmera já liberada (milhares de avisos MSMF) e pode disputar o
    dispositivo com a tomada seguinte, derrubando o fps.
    """
    dataset = getattr(getattr(model, "predictor", None), "dataset", None)
    close = getattr(dataset, "close", None)
    if close is not None:
        close()


def reset_tracker(model: Any) -> None:
    """Descarta o predictor (e o estado do botsort) para IDs não vazarem entre takes."""
    close_stream(model)
    model.predictor = None


def _is_untracked(result: Any) -> bool:
    """Há detecções mas o tracker não devolveu IDs (zero tracks no frame)."""
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return False
    return getattr(boxes, "id", None) is None


def iter_pose_frames(model: Any, source: int | str, kwargs: dict[str, Any], clock: str = "wall") -> Iterator[PoseFrame]:
    """`clock='wall'`: timestamps reais (igual ao deploy). `clock='video'`:
    posição no vídeo (frame_idx/fps), para replay determinístico."""
    from capture.pose_extract import unpack_raw_points

    video_fps = native_fps(source) if clock == "video" and isinstance(source, str) else None
    gen = model.track(source, **kwargs)
    t_ready = time.perf_counter()          # início da espera pelo 1º resultado
    try:
        for i, result in enumerate(gen):
            wait_ms = (time.perf_counter() - t_ready) * 1000.0
            if clock == "video":
                t_wall = t_mono = i / (video_fps or 30.0)
            else:
                t_wall, t_mono = time.time(), time.monotonic()   # pós-YOLO, como o deploy
            speed = getattr(result, "speed", None) or {}
            yolo_ms = float(sum(speed.get(k, 0.0) for k in ("preprocess", "inference", "postprocess")))
            yield PoseFrame(
                observations=unpack_raw_points(result, timestamp=t_wall),
                image=getattr(result, "orig_img", None),
                yolo_ms=yolo_ms,
                t_wall=t_wall,
                t_mono=t_mono,
                untracked=_is_untracked(result),
                wait_ms=wait_ms,
            )
            t_ready = time.perf_counter()   # o consumidor roda até o gerador ser retomado
    finally:
        gen.close()
        close_stream(model)
