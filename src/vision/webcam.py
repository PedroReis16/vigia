"""Orquestração do preview: fonte de frames, captura, pipeline de sequência e exibição."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from src.ml.yolo_detector import YOLODetector
from src.vision.capture_handler import CaptureHandler, CaptureResult
from src.vision.frame_source import create_frame_source
from src.vision.preview_config import PreviewConfig
from src.vision.preview_display import PreviewDisplay
from src.vision.sequence_pipeline import SequencePipeline
from src.vision.yolo_features import save_sequence_for_lstm

logger = logging.getLogger(__name__)


class WebcamPreviewService:
    """Orquestra preview de câmera/vídeo com captura de sequências para LSTM.

    Não concentra mais toda a lógica: delega para:
    - Frame source (câmera ou vídeo) via create_frame_source
    - CaptureHandler: buffers e decisão de quando capturar
    - SequencePipeline: frames → YOLO → sequência
    - PreviewDisplay: janela e overlays
    """

    def __init__(
        self,
        camera_index: int | list[int] = 0,
        window_name: str = "older-fall webcam",
        flip_horizontal: bool = False,
        yolo_model_path: str = "yolov8s.pt",
        detection_conf: float = 0.7,
        detection_imgsz: int = 640,
        *,
        video_source: str | Path | None = None,
        frames_to_capture: int = 30,
        capture_output_dir: str | Path = "data/captures",
        save_frames: bool = False,
        capture_key: int = ord("c"),
        continuous_capture: bool = False,
        capture_interval_frames: int = 1,
        on_sequence_ready: Callable[[np.ndarray], None] | None = None,
        save_continuous_sequences: bool = False,
    ) -> None:
        """Inicializa o serviço a partir dos mesmos parâmetros de antes.

        Os argumentos são agrupados em PreviewConfig e os componentes
        (fonte, pipeline, captura, display) são criados internamente.
        """
        self._config = PreviewConfig(
            camera_index=camera_index,
            video_source=Path(video_source) if isinstance(video_source, str) else video_source,
            window_name=window_name,
            flip_horizontal=flip_horizontal,
            yolo_model_path=yolo_model_path,
            detection_conf=detection_conf,
            detection_imgsz=detection_imgsz,
            frames_to_capture=frames_to_capture,
            capture_output_dir=capture_output_dir,
            save_frames=save_frames,
            capture_key=capture_key,
            continuous_capture=continuous_capture,
            capture_interval_frames=capture_interval_frames,
            on_sequence_ready=on_sequence_ready,
            save_continuous_sequences=save_continuous_sequences,
        )
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_save_message: str | None = None
        self._last_save_frames_left = 0
        self._save_message_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="webcam_save")

        # Componentes (injetados / criados a partir do config)
        self._frame_source = create_frame_source(
            self._config.camera_indices,
            self._config.video_source,
        )
        self._detector = YOLODetector(self._config.yolo_model_path)
        self._sequence_pipeline = SequencePipeline(
            self._detector,
            imgsz=self._config.detection_imgsz,
            conf=self._config.detection_conf,
            device="cpu",
        )
        self._capture_handler = CaptureHandler(self._config)
        self._display = PreviewDisplay(
            self._config.window_name,
            is_debug_video=self._config.is_debug_video,
        )

    def start(self) -> None:
        """Inicia o preview em thread de background."""
        if self._running:
            logger.warning("Preview já está em execução")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Preview da webcam iniciado em background")

    def run_blocking(self) -> None:
        """Inicia o preview no thread atual (bloqueante)."""
        if self._running:
            logger.warning("Preview já está em execução")
            return
        self._running = True
        logger.info("Preview da webcam iniciado em modo bloqueante")
        self._run_loop()

    def stop(self) -> None:
        """Para o preview e libera recursos."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._executor.shutdown(wait=True)
        self._frame_source.release()
        self._display.destroy()
        logger.info("Preview da webcam finalizado")

    def _run_loop(self) -> None:
        """Loop principal: lê frame, atualiza captura, exibe e processa teclas."""
        if self._detector.model is None:
            logger.error("Falha ao carregar modelo YOLO")
            self._running = False
            return
        if not self._frame_source.open():
            logger.error("Falha ao abrir fonte de frames (câmera ou vídeo)")
            self._running = False
            return

        self._display.open()
        logger.info("Loop de detecção iniciado")

        key = -1
        frame_count = 0

        try:
            while self._running:
                if not self._display.is_visible():
                    logger.info("Janela foi fechada pelo usuário")
                    self._running = False
                    break

                ret, frame = self._frame_source.read()
                if not ret or frame is None:
                    continue

                if self._config.flip_horizontal:
                    frame = cv2.flip(frame, 1)
                h_frame, w_frame = frame.shape[:2]

                result, overlays = self._capture_handler.update(
                    frame, key, w_frame, h_frame
                )

                if result is not None:
                    self._dispatch_capture(result)

                with self._save_message_lock:
                    msg = self._last_save_message
                    left = self._last_save_frames_left
                if left > 0 and msg:
                    with self._save_message_lock:
                        self._last_save_frames_left = left - 1

                self._display.show(
                    frame,
                    overlays,
                    save_message=msg if left > 0 else None,
                    save_message_frames_left=left,
                )

                frame_count += 1
                if frame_count % 10 == 0:
                    print(
                        "Processando frame {}... (Pressione 'c' para capturar sequência para LSTM)".format(
                            frame_count
                        )
                    )

                key = self._display.wait_key(1)
                if key in (27, ord("q")):
                    logger.info("Tecla de saída pressionada")
                    self._running = False
                    break

        except Exception:
            logger.exception("Erro no loop de detecção")
        finally:
            self._frame_source.release()
            self._display.destroy()
            self._running = False
            logger.info("Loop de detecção finalizado")

    def _dispatch_capture(self, result: CaptureResult) -> None:
        """Envia a captura para processamento em background (manual ou contínuo)."""
        if result.is_continuous:
            self._executor.submit(
                self._run_save_task,
                result,
                continuous_window_index=result.continuous_window_index,
            )
        else:
            out_dir = self._capture_handler.manual_output_dir()
            out_dir.mkdir(parents=True, exist_ok=True)
            with self._save_message_lock:
                self._last_save_message = "Salvando em background..."
                self._last_save_frames_left = 90
            self._executor.submit(
                self._run_save_task,
                result,
                manual_out_dir=out_dir,
                manual_save_frames=result.manual_save_frames,
            )

    def _run_save_task(
        self,
        result: CaptureResult,
        *,
        continuous_window_index: int | None = None,
        manual_out_dir: Path | None = None,
        manual_save_frames: bool = False,
    ) -> None:
        """Executado em thread: gera sequência, salva e/ou chama callback."""
        sequence = self._sequence_pipeline.build_sequence(
            result.frames,
            result.frame_width,
            result.frame_height,
        )
        if sequence is None:
            return

        if continuous_window_index is not None:
            n = continuous_window_index
            if self._config.save_continuous_sequences:
                cont_dir = self._config.capture_output_path / "continuous"
                cont_dir.mkdir(parents=True, exist_ok=True)
                path_npy = cont_dir / f"seq_{n:06d}.npy"
                save_sequence_for_lstm(sequence, path_npy, fmt="npy")
                print(f"[LSTM] Janela #{n} -> salva em {path_npy} (shape {sequence.shape})")
            if self._config.on_sequence_ready is not None:
                try:
                    self._config.on_sequence_ready(sequence)
                    print(f"[LSTM] Janela #{n} (shape {sequence.shape}) enviada para callback")
                except Exception:
                    logger.exception("Erro no callback on_sequence_ready")
            elif not self._config.save_continuous_sequences:
                print(
                    f"[LSTM] Janela #{n} (shape {sequence.shape}) "
                    "[configure on_sequence_ready ou save_continuous_sequences=True]"
                )
            return

        if manual_out_dir is not None:
            if manual_save_frames:
                frames_dir = manual_out_dir / "frames"
                frames_dir.mkdir(parents=True, exist_ok=True)
                for i, f in enumerate(result.frames):
                    cv2.imwrite(str(frames_dir / f"frame_{i:04d}.jpg"), f)
            save_sequence_for_lstm(sequence, manual_out_dir / "sequence.npy", fmt="npy")
            save_sequence_for_lstm(sequence, manual_out_dir / "sequence.csv", fmt="csv")
            logger.info("Sequência para LSTM salva em %s (shape %s)", manual_out_dir, sequence.shape)
            print(f"[LSTM] Captura manual salva em {manual_out_dir} (shape {sequence.shape})")
            with self._save_message_lock:
                self._last_save_message = f"Salvo em {manual_out_dir}"
                self._last_save_frames_left = 90
