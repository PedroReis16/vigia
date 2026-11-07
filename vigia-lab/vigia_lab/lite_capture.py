"""Captura leve: só lê a câmera e grava vídeo (sem YOLO, sem desenho de esqueleto).

Uma thread lê a câmera o mais rápido possível, guarda o último frame para o preview e,
durante a gravação, entrega cada frame ao `VideoSink` (thread própria) e registra o
timestamp SÓ dos frames aceitos pelo sink — assim vídeo e `_frames.npz` ficam alinhados.
A câmera é aberta quando a tomada começa e fechada ao final (o MSMF do Windows invalida
o dispositivo depois de minutos ocioso).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from vigia_lab.sidecar import FrameClock
from vigia_lab.video_sink import VideoSink

DEFAULT_RESOLUTION = (640, 480)
DEFAULT_FPS = 30
VIDEO_QUALITY = 95


@dataclass
class RecordingResult:
    clock: FrameClock
    dropped: int
    video_path: Path
    resolution: tuple[int, int]
    nominal_fps: float | None


@dataclass
class _Recording:
    sink: VideoSink
    path: Path
    t_mono: list[float] = field(default_factory=list)
    t_wall: list[float] = field(default_factory=list)
    brightness: list[float] = field(default_factory=list)


def _open_camera(index: int) -> Any:
    import cv2

    return cv2.VideoCapture(index)


class LiteCamera:
    def __init__(
        self,
        index: int = 0,
        resolution: tuple[int, int] = DEFAULT_RESOLUTION,
        fps: int = DEFAULT_FPS,
        cap_factory: Callable[[int], Any] = _open_camera,
        use_mjpg: bool = True,
    ) -> None:
        self._index = index
        self._resolution = resolution
        self._fps = fps
        self._factory = cap_factory
        self._use_mjpg = use_mjpg
        self._cap: Any = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._latest: tuple[np.ndarray, float] | None = None
        self._rec: _Recording | None = None
        self._recent: list[float] = []
        self.error: str | None = None
        self.nominal_fps: float | None = None

    # ---------------------------------------------------------------- ciclo de vida
    def open(self) -> bool:
        import cv2

        self._cap = self._factory(self._index)
        if not self._cap.isOpened():
            self.error = "camera nao abriu"
            return False
        if self._use_mjpg:
            self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._resolution[0])
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._resolution[1])
        self._cap.set(cv2.CAP_PROP_FPS, self._fps)
        reported = float(self._cap.get(cv2.CAP_PROP_FPS) or 0)
        self.nominal_fps = reported if reported > 0 else None
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="lab-camera", daemon=True)
        self._thread.start()
        return True

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
        if self._cap is not None:
            self._cap.release()
        self._cap = None

    # ---------------------------------------------------------------- leitura
    def _run(self) -> None:
        failures = 0
        while not self._stop.is_set():
            ok, frame = self._cap.read()
            now_m, now_w = time.monotonic(), time.time()
            if not ok or frame is None:
                failures += 1
                if failures > 30:
                    self.error = "camera parou de entregar frames"
                    return
                time.sleep(0.01)
                continue
            failures = 0
            with self._lock:
                self._latest = (frame, now_m)
                self._recent.append(now_m)
                del self._recent[:-30]
                rec = self._rec
            if rec is not None and rec.sink.write(frame):
                rec.t_mono.append(now_m)
                rec.t_wall.append(now_w)
                rec.brightness.append(float(frame[::16, ::16].mean()))

    def latest(self) -> tuple[np.ndarray, float] | None:
        with self._lock:
            return self._latest

    def live_fps(self) -> float:
        with self._lock:
            r = list(self._recent)
        return (len(r) - 1) / (r[-1] - r[0]) if len(r) > 2 and r[-1] > r[0] else 0.0

    # ---------------------------------------------------------------- gravação
    def begin_recording(self, video_path: Path) -> None:
        snap = self.latest()
        if snap is None:
            raise RuntimeError("sem frames da camera ainda")
        h, w = snap[0].shape[:2]
        sink = VideoSink(video_path, self.nominal_fps or float(self._fps), (w, h), quality=VIDEO_QUALITY)
        with self._lock:
            self._rec = _Recording(sink=sink, path=video_path)

    def recorded_seconds(self) -> float:
        with self._lock:
            rec = self._rec
        return rec.t_mono[-1] - rec.t_mono[0] if rec is not None and len(rec.t_mono) > 1 else 0.0

    def recording_t0(self) -> float | None:
        with self._lock:
            rec = self._rec
        return rec.t_mono[0] if rec is not None and rec.t_mono else None

    def end_recording(self) -> RecordingResult:
        with self._lock:
            rec, self._rec = self._rec, None
        if rec is None:
            raise RuntimeError("nenhuma gravacao em andamento")
        rec.sink.close()
        h, w = self._latest[0].shape[:2] if self._latest else (0, 0)
        return RecordingResult(
            clock=FrameClock(
                np.array(rec.t_mono, dtype=np.float64),
                np.array(rec.t_wall, dtype=np.float64),
                np.array(rec.brightness, dtype=np.float32),
            ),
            dropped=rec.sink.drops,
            video_path=rec.path,
            resolution=(w, h),
            nominal_fps=self.nominal_fps,
        )
