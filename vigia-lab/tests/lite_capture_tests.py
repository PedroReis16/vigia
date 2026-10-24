import time
from pathlib import Path

import cv2
import numpy as np

from vigia_lab.lite_capture import LiteCamera
from vigia_lab.sidecar import FrameClock, load_capture_meta, load_frames, save_capture_meta, save_frames, sidecar_paths


class FakeCap:
    """Câmera sintética a ~100 fps: frame i tem brilho constante e tamanho fixo."""

    def __init__(self, fail_after: int | None = None) -> None:
        self.n = 0
        self.props: dict[int, float] = {}
        self.fail_after = fail_after
        self.released = False

    def isOpened(self) -> bool:
        return True

    def set(self, prop, value) -> bool:
        self.props[prop] = value
        return True

    def get(self, prop) -> float:
        return 30.0 if prop == cv2.CAP_PROP_FPS else 0.0

    def read(self):
        time.sleep(0.01)
        self.n += 1
        if self.fail_after is not None and self.n > self.fail_after:
            return False, None
        return True, np.full((48, 64, 3), 100, dtype=np.uint8)

    def release(self) -> None:
        self.released = True


def test_timestamps_align_with_video_frames(tmp_path: Path) -> None:
    cam = LiteCamera(cap_factory=lambda _i: FakeCap())
    assert cam.open() and cam.nominal_fps == 30.0
    while cam.latest() is None:
        time.sleep(0.005)
    cam.begin_recording(tmp_path / "t.avi")
    time.sleep(0.6)
    res = cam.end_recording()
    cam.close()

    cap = cv2.VideoCapture(str(tmp_path / "t.avi"))
    n_video = 0
    while cap.read()[0]:
        n_video += 1
    cap.release()
    assert len(res.clock) == n_video > 20                # 1 timestamp por frame do vídeo
    assert np.all(np.diff(res.clock.t_mono) > 0) and res.dropped == 0
    assert abs(res.clock.brightness.mean() - 100) < 3 and res.resolution == (64, 48)


def test_camera_failure_sets_error_and_close_releases(tmp_path: Path) -> None:
    fake = FakeCap(fail_after=5)
    cam = LiteCamera(cap_factory=lambda _i: fake)
    cam.open()
    deadline = time.time() + 3
    while cam.error is None and time.time() < deadline:
        time.sleep(0.02)
    cam.close()
    assert cam.error == "camera parou de entregar frames" and fake.released


def test_sidecar_roundtrip(tmp_path: Path) -> None:
    clock = FrameClock(np.array([10.0, 10.04, 10.09]), np.array([1e9, 1e9 + 0.04, 1e9 + 0.09]), np.array([90.0, 91.0, 92.0], dtype=np.float32))
    paths = sidecar_paths(tmp_path / "x_take01.avi")
    save_frames(paths["frames"], clock)
    back = load_frames(paths["frames"])
    np.testing.assert_allclose(back.t_rel, [0.0, 0.04, 0.09])
    save_capture_meta(paths["capture"], {"marks": {"event_start_t": 2.5}, "p": tmp_path})
    assert load_capture_meta(paths["capture"])["marks"]["event_start_t"] == 2.5
    assert paths["frames"].name == "x_take01_frames.npz"
