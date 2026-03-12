"""Webcam preview service with YOLO detection - optimized and modular."""

import logging
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from src.ml.yolo_detector import YOLODetector
from src.vision.camera import CameraManager
from src.vision.renderer import DetectionRenderer
from src.vision.yolo_features import (
    extract_features_from_results,
    features_per_frame_to_sequence,
    save_sequence_for_lstm,
)

logger = logging.getLogger(__name__)


class WebcamPreviewService:
    """Service for displaying webcam feed with real-time YOLO detections."""

    def __init__(
        self,
        camera_index: int | list[int] = 0,
        window_name: str = "older-fall webcam",
        flip_horizontal: bool = False,
        yolo_model_path: str = "yolov8s.pt",
        detection_conf: float = 0.7,
        detection_imgsz: int = 640,
        *,
        frames_to_capture: int = 30,
        capture_output_dir: str | Path = "data/captures",
        save_frames: bool = False,
        capture_key: int = ord("c"),
        continuous_capture: bool = False,
        capture_interval_frames: int = 1,
        on_sequence_ready: Callable[[np.ndarray], None] | None = None,
        save_continuous_sequences: bool = False,
    ) -> None:
        """Initialize webcam preview service.

        Args:
            camera_index: Camera index or list of indices to try
            window_name: Name for the display window
            flip_horizontal: Whether to flip frames horizontally
            yolo_model_path: Path to YOLO model
            detection_conf: Confidence threshold for detections
            detection_imgsz: Input image size for YOLO
            frames_to_capture: Frames per window (manual: 30; contínuo/câmera segurança: 8–16).
            capture_output_dir: Directory to save frames/sequence (modo manual).
            save_frames: Save frame images when capturing (modo manual).
            capture_key: Key to start manual capture (default: 'c').
            continuous_capture: Se True, amostragem contínua automática (janela deslizante).
            capture_interval_frames: Em modo contínuo, processar janela a cada N frames (1=todo frame).
            on_sequence_ready: Callback(sequence) chamado a cada janela no modo contínuo (para LSTM/queda).
            save_continuous_sequences: Se True, no modo contínuo salva cada sequência em disco (para ver que está gravando).
        """
        camera_indices = [camera_index] if isinstance(camera_index, int) else camera_index

        self._window_name = window_name
        self._flip_horizontal = flip_horizontal
        self._detection_conf = detection_conf
        self._detection_imgsz = detection_imgsz
        self._running = False
        self._thread: threading.Thread | None = None

        # Capture para LSTM
        self._frames_to_capture = max(1, frames_to_capture)
        self._capture_output_dir = Path(capture_output_dir)
        self._save_frames = save_frames
        self._capture_key = capture_key
        self._capturing = False
        self._frame_buffer: list = []

        # Modo contínuo (câmera de segurança)
        self._continuous_capture = continuous_capture
        self._capture_interval_frames = max(1, capture_interval_frames)
        self._on_sequence_ready = on_sequence_ready
        self._sliding_buffer: deque = deque(maxlen=self._frames_to_capture)
        self._frames_since_process = 0
        self._windows_processed_count = 0  # feedback: quantas janelas já foram processadas
        self._save_continuous_sequences = save_continuous_sequences

        # Feedback pós-save (modo manual): mostrar "Salvo em ..." na tela por alguns segundos
        self._last_save_message: str | None = None
        self._last_save_frames_left = 0
        self._save_message_lock = threading.Lock()

        # Processamento e save em background (evita delay na imagem)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="webcam_save")

        # Initialize components (lazy loading)
        self._camera = CameraManager(camera_indices, timeout_ms=1000)
        self._detector = YOLODetector(yolo_model_path)
        self._renderer = DetectionRenderer(show_labels=False, show_conf=False)

    def start(self) -> None:
        """Start webcam preview in background thread."""
        if self._running:
            logger.warning("Preview já está em execução")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Preview da webcam iniciado em background")

    def run_blocking(self) -> None:
        """Start webcam preview in blocking mode (current thread)."""
        if self._running:
            logger.warning("Preview já está em execução")
            return

        self._running = True
        logger.info("Preview da webcam iniciado em modo bloqueante")
        self._run_loop()

    def stop(self) -> None:
        """Stop webcam preview and release resources."""
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        self._executor.shutdown(wait=True)
        self._camera.release()
        cv2.destroyAllWindows()
        logger.info("Preview da webcam finalizado")

    def _run_loop(self) -> None:
        """Main processing loop - simplified and optimized."""
        # Lazy load model (only once)
        if self._detector.model is None:
            logger.error("Falha ao carregar modelo YOLO")
            self._running = False
            return

        # Open camera with fallback
        if not self._camera.open():
            logger.error("Falha ao abrir câmera")
            self._running = False
            return

        # Create resizable window
        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        # logger.info("Janela criada com suporte a redimensionamento")
        logger.info("Loop de detecção iniciado")

        try:
            frame_count = 0
            h_frame, w_frame = 0, 0

            while self._running:
                # Check if window was closed by user (X button)
                if cv2.getWindowProperty(self._window_name, cv2.WND_PROP_VISIBLE) < 1:
                    logger.info("Janela foi fechada pelo usuário")
                    self._running = False
                    break

                # Read frame
                ret, frame = self._camera.read()
                if not ret or frame is None:
                    continue

                # Flip if needed
                if self._flip_horizontal:
                    frame = cv2.flip(frame, 1)

                h_frame, w_frame = frame.shape[:2]

                # --- Modo contínuo: janela deslizante, amostragem automática ---
                if self._continuous_capture:
                    self._sliding_buffer.append(frame.copy())
                    if len(self._sliding_buffer) == self._frames_to_capture:
                        self._frames_since_process += 1
                        if self._frames_since_process >= self._capture_interval_frames:
                            self._frames_since_process = 0
                            self._windows_processed_count += 1
                            n = self._windows_processed_count
                            frames_copy = list(self._sliding_buffer)
                            self._executor.submit(
                                self._run_save_task,
                                frames_copy,
                                w_frame,
                                h_frame,
                                continuous_window_index=n,
                            )
                    # Overlay indicando modo contínuo e quantas janelas já foram processadas
                    overlay = frame.copy()
                    cv2.putText(
                        overlay,
                        f"Continuo [buffer={len(self._sliding_buffer)}/{self._frames_to_capture}]",
                        (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2,
                    )
                    cv2.putText(
                        overlay,
                        f"Janelas processadas: {self._windows_processed_count}",
                        (10, 75),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
                    if self._save_continuous_sequences:
                        cv2.putText(
                            overlay,
                            "Salvando em data/captures/continuous/",
                            (10, 115),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            2,
                        )
                    cv2.imshow(self._window_name, overlay)
                    frame_count += 1
                    key = cv2.waitKey(1) & 0xFF
                    if key in (27, ord("q")):
                        self._running = False
                        break
                    continue

                # --- Modo manual: buffer de N frames ao pressionar 'c' ---
                if self._capturing:
                    self._frame_buffer.append(frame.copy())
                    n = len(self._frame_buffer)
                    if n >= self._frames_to_capture:
                        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        out_dir = self._capture_output_dir / stamp
                        out_dir.mkdir(parents=True, exist_ok=True)
                        frames_copy = list(self._frame_buffer)
                        self._executor.submit(
                            self._run_save_task,
                            frames_copy,
                            w_frame,
                            h_frame,
                            manual_out_dir=out_dir,
                            manual_save_frames=self._save_frames,
                        )
                        self._capturing = False
                        self._frame_buffer.clear()
                        # Mostra "Salvando em background..." na tela
                        with self._save_message_lock:
                            self._last_save_message = "Salvando em background..."
                            self._last_save_frames_left = 90
                    else:
                        overlay = frame.copy()
                        cv2.putText(
                            overlay,
                            f"Capturando {n}/{self._frames_to_capture} (LSTM)",
                            (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.0,
                            (0, 255, 0),
                            2,
                        )
                        cv2.imshow(self._window_name, overlay)
                        frame_count += 1
                        key = cv2.waitKey(1) & 0xFF
                        if key in (27, ord("q")):
                            self._running = False
                            break
                        continue

                # Tecla 'c' inicia captura dos próximos N frames
                key = cv2.waitKey(1) & 0xFF
                if key == self._capture_key and not self._capturing:
                    self._capturing = True
                    self._frame_buffer = []
                    logger.info("Captura iniciada: próximos %d frames", self._frames_to_capture)

                # Preview normal (sem YOLO em tempo real para performance)
                display = frame.copy()
                with self._save_message_lock:
                    msg = self._last_save_message
                    left = self._last_save_frames_left
                if left > 0 and msg:
                    cv2.putText(
                        display,
                        msg,
                        (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
                    cv2.putText(
                        display,
                        "Sequencia salva para LSTM" if "Salvo" in msg else "Salvando em background...",
                        (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
                    with self._save_message_lock:
                        self._last_save_frames_left = left - 1
                cv2.imshow(self._window_name, display)

                frame_count += 1

                if frame_count % 10 == 0:
                    print(f"Processando frame {frame_count}... (Pressione 'c' para capturar sequência para LSTM)")

                # Check for quit key (ESC or 'q')
                if key in (27, ord("q")):
                    logger.info("Tecla de saída pressionada")
                    self._running = False
                    break

        except Exception:
            logger.exception("Erro no loop de detecção")
        finally:
            self._camera.release()
            cv2.destroyAllWindows()
            self._running = False
            logger.info("Loop de detecção finalizado")

    def _run_save_task(
        self,
        frames: list,
        frame_width: int,
        frame_height: int,
        *,
        continuous_window_index: int | None = None,
        manual_out_dir: Path | None = None,
        manual_save_frames: bool = False,
    ) -> None:
        """Roda em thread separada: YOLO -> sequência -> save/callback (não bloqueia a imagem)."""
        sequence = self._buffer_to_sequence(frames, frame_width, frame_height)
        if sequence is None:
            return

        if continuous_window_index is not None:
            n = continuous_window_index
            if self._save_continuous_sequences:
                cont_dir = self._capture_output_dir / "continuous"
                cont_dir.mkdir(parents=True, exist_ok=True)
                path_npy = cont_dir / f"seq_{n:06d}.npy"
                save_sequence_for_lstm(sequence, path_npy, fmt="npy")
                print(f"[LSTM] Janela #{n} -> salva em {path_npy} (shape {sequence.shape})")
            if self._on_sequence_ready is not None:
                try:
                    self._on_sequence_ready(sequence)
                    print(f"[LSTM] Janela #{n} (shape {sequence.shape}) enviada para callback")
                except Exception:
                    logger.exception("Erro no callback on_sequence_ready")
            elif not self._save_continuous_sequences:
                print(f"[LSTM] Janela #{n} (shape {sequence.shape}) [configure on_sequence_ready ou save_continuous_sequences=True]")
            return

        if manual_out_dir is not None:
            frames_dir = manual_out_dir / "frames"
            if manual_save_frames:
                frames_dir.mkdir(parents=True, exist_ok=True)
                for i, f in enumerate(frames):
                    cv2.imwrite(str(frames_dir / f"frame_{i:04d}.jpg"), f)
            save_sequence_for_lstm(sequence, manual_out_dir / "sequence.npy", fmt="npy")
            save_sequence_for_lstm(sequence, manual_out_dir / "sequence.csv", fmt="csv")
            logger.info("Sequência para LSTM salva em %s (shape %s)", manual_out_dir, sequence.shape)
            print(f"[LSTM] Captura manual salva em {manual_out_dir} (shape {sequence.shape})")
            with self._save_message_lock:
                self._last_save_message = f"Salvo em {manual_out_dir}"
                self._last_save_frames_left = 90

    def _buffer_to_sequence(
        self,
        frames: list,
        frame_width: int,
        frame_height: int,
    ) -> np.ndarray | None:
        """Roda YOLO nos frames e retorna sequência (n_frames, n_features) para LSTM."""
        if not frames:
            return None
        features_per_frame: list[list[dict]] = []
        for frame in frames:
            results = self._detector.predict(
                source=frame,
                imgsz=self._detection_imgsz,
                conf=self._detection_conf,
                device="cpu",
                verbose=False,
            )
            feats = extract_features_from_results(
                results,
                frame_width=frame_width,
                frame_height=frame_height,
                normalize=True,
                max_detections=1,
            )
            features_per_frame.append(feats)
        return features_per_frame_to_sequence(
            features_per_frame,
            keys=("center_x", "center_y", "width", "height", "conf"),
            pick_best=True,
        )

    def _process_captured_frames(self, frame_width: int, frame_height: int) -> None:
        """Envia processamento e save para thread em background (não bloqueia a imagem)."""
        if not self._frame_buffer:
            return
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_dir = self._capture_output_dir / stamp
        out_dir.mkdir(parents=True, exist_ok=True)
        frames_copy = list(self._frame_buffer)
        self._executor.submit(
            self._run_save_task,
            frames_copy,
            frame_width,
            frame_height,
            manual_out_dir=out_dir,
            manual_save_frames=self._save_frames,
        )
        with self._save_message_lock:
            self._last_save_message = "Salvando em background..."
            self._last_save_frames_left = 90