"""
Pacote de captura (subpastas por responsabilidade):

- ``pose/`` — tipos de keypoint, modelo YOLO, CSV e worker de inferência.
- ``loop/`` — loop de vídeo (câmera, fila pose, stream, preview).
- ``io/`` — workers de disco/stream e gravação por sessão em pastas.
- ``roi/`` — recorte de região de interesse no frame.
"""

from .runner import run_capture

__all__ = ["run_capture"]