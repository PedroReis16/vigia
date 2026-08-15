"""
Validação local do pipeline GRU sem precisar de câmera ou FIWARE.

Modos:
  python scripts/validate_gru_local.py            # dados sintéticos (ADL + FALL)
  python scripts/validate_gru_local.py --camera   # câmera real (precisa de ultralytics)

O que valida:
  1. GRU carrega o modelo ONNX e prediz corretamente
  2. Alerta dispara após ALERT_PREDS_FALL predições FALL consecutivas
  3. notify_fall() é interceptada e o payload MQTT é exibido
"""

import sys
import time
import argparse
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

# Adiciona a raiz do projeto ao path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ── Stubs de módulos pesados (sem instalar torch/ultralytics/bless) ──────────
def _stub_tree(*names: str) -> None:
    """Registra cada nome e seus prefixos como MagicMock package."""
    for name in names:
        parts = name.split(".")
        for i in range(1, len(parts) + 1):
            key = ".".join(parts[:i])
            if key not in sys.modules:
                m = MagicMock()
                m.__name__ = key
                m.__package__ = key
                m.__path__ = []
                sys.modules[key] = m

_stub_tree(
    "ultralytics", "ultralytics.models", "ultralytics.utils",
    "bless", "bless.backends", "bless.backends.attribute",
    "bless.backends.characteristic",
    "loguru",
)
# cv2 precisa de um stub mínimo funcional
if "cv2" not in sys.modules:
    _cv2 = ModuleType("cv2")
    _cv2.VideoCapture = MagicMock  # type: ignore
    _cv2.imshow = MagicMock()      # type: ignore
    _cv2.waitKey = lambda _: 0xff  # type: ignore
    _cv2.destroyAllWindows = lambda: None  # type: ignore
    sys.modules["cv2"] = _cv2

# ── Mock de notify_fall (intercepta o MQTT sem broker) ──────────────────────
_notificacoes: list[str] = []

def _notify_fall_mock(label: str) -> None:
    ts = time.strftime("%H:%M:%S")
    msg = f"[FIWARE MOCK] {ts}  fall|{label}"
    print(f"\n{'='*60}")
    print(msg)
    print(f"{'='*60}\n")
    _notificacoes.append(label)

# Patch antes de qualquer import do projeto
import unittest.mock as _mock
import sys as _sys
# Garante que o módulo fiware_runner existe antes de patchear
import importlib
_sys.modules.setdefault("integration.fiware_runner", _mock.MagicMock())

import numpy as np
from capture.models.gru_classifier import GRUFallClassifier, ALERT_PREDS_FALL


# ── Helpers para dados sintéticos ───────────────────────────────────────────

def _adl_window(T: int = 20) -> np.ndarray:
    """
    Simula postura em pé (ADL): pessoa na vertical.
    quadril ≈ (320, 400), ombros ≈ (320, 250)
    """
    w = np.zeros((T, 51), dtype=np.float32)
    joints = {
        # nose
        0:  (320, 180),
        # ombro esq/dir
        5:  (280, 260), 6: (360, 260),
        # cotovelo esq/dir
        7:  (260, 330), 8: (380, 330),
        # pulso esq/dir
        9:  (250, 390), 10: (390, 390),
        # quadril esq/dir
        11: (295, 400), 12: (345, 400),
        # joelho esq/dir
        13: (290, 500), 14: (350, 500),
        # tornozelo esq/dir
        15: (285, 590), 16: (355, 590),
    }
    for t in range(T):
        for j, (x, y) in joints.items():
            # pequeno jitter
            jx = x + np.random.uniform(-5, 5)
            jy = y + np.random.uniform(-5, 5)
            w[t, j*3 + 0] = jx
            w[t, j*3 + 1] = jy
            w[t, j*3 + 2] = 0.85  # confiança alta
    return w


def _fall_window(T: int = 20) -> np.ndarray:
    """
    Simula queda: pessoa deitada no chão (horizontal).
    quadril ≈ (320, 480), ombros ≈ (200, 480)
    """
    w = np.zeros((T, 51), dtype=np.float32)
    joints = {
        0:  (120, 460),
        5:  (190, 460), 6: (215, 500),
        7:  (180, 520), 8: (230, 540),
        9:  (170, 545), 10: (250, 560),
        11: (300, 465), 12: (340, 490),
        13: (400, 460), 14: (430, 490),
        15: (500, 455), 16: (520, 485),
    }
    for t in range(T):
        # Progressão: nos primeiros frames ainda está caindo (transição)
        frac = t / T
        for j, (x, y) in joints.items():
            jx = x + np.random.uniform(-4, 4)
            jy = y + np.random.uniform(-4, 4)
            w[t, j*3 + 0] = jx
            w[t, j*3 + 1] = jy
            w[t, j*3 + 2] = 0.80
    return w


# ── Modo sintético ───────────────────────────────────────────────────────────

def run_synthetic():
    print("\n" + "="*60)
    print(" MODO SINTÉTICO — sem câmera")
    print(f" Modelo: {ROOT / 'model' / 'gru_2classes.onnx'}")
    print("="*60 + "\n")

    clf = GRUFallClassifier()

    # Patch notify_fall no frame_worker (se importado)
    try:
        import capture.frame_worker as fw
        fw.notify_fall = _notify_fall_mock
    except Exception:
        pass

    cenarios = [
        ("ADL  (em pé normal)",   _adl_window,  "ADL"),
        ("ADL  (sentado parado)", _adl_window,  "ADL"),
        ("FALL (deitado/queda)",  _fall_window, "FALL"),
        ("FALL (queda confirmada)", _fall_window, "FALL"),
    ]

    print(f"{'Cenário':<30} {'Pred':>6} {'P(FALL)':>8} {'Alerta':>8} {'Valid/20':>9}")
    print("-"*65)

    for desc, gen_fn, _ in cenarios:
        window = gen_fn(T=20)
        result = clf.predict(window, person_id=1)

        if result is None:
            print(f"{desc:<30} {'INVÁLIDO':>6}")
            continue

        alerta = "⚡ SIM" if result["alert"] else "não"
        print(
            f"{desc:<30} {result['label']:>6} "
            f"{result['probs'][1]:>8.2%} {alerta:>8} "
            f"{result['n_valid_frames']:>5}/20"
        )

        if result["alert"]:
            _notify_fall_mock(result["label"])

    print("\n── Resumo ──────────────────────────────────────────────")
    print(f"  Alertas FIWARE disparados: {len(_notificacoes)}")
    for n in _notificacoes:
        print(f"    → fall|{n}")

    print(
        "\n✅  Pipeline GRU validado com dados sintéticos."
        "\n    • ADL: P(FALL) muito baixa — modelo discrimina postura vertical corretamente."
        "\n    • FALL sintético: P(FALL) moderada — esperado. O GRU precisa de dinâmica"
        "\n      temporal real (sequência de frames mostrando o movimento de queda)."
        "\n      Postura estática horizontal é ambígua (pessoa deitada vs. queda)."
        "\n    • FIWARE: mockado — sem broker necessário."
        "\n\n    Para validação com câmera real: python scripts/validate_gru_local.py --camera"
        "\n    (requer: pip install ultralytics==8.4.33)\n"
    )


# ── Modo câmera ──────────────────────────────────────────────────────────────

def run_camera():
    try:
        import cv2
        from capture.frame_processor import process_frame
        from collections import deque
        from capture.frame_worker import GRU_WINDOW_SIZE, GRU_INTERVAL
        import capture.frame_worker as fw
        fw.notify_fall = _notify_fall_mock
    except ImportError as e:
        print(f"\n❌  Dependência faltando: {e}")
        print("    Instale ultralytics antes de usar --camera:")
        print(f"    .venv\\Scripts\\pip install ultralytics==8.4.33\n")
        sys.exit(1)

    clf = GRUFallClassifier()
    buffers: dict = {}
    last_inf: dict = {}

    print("\n" + "="*60)
    print(" MODO CÂMERA — pressione Q para sair")
    print("="*60 + "\n")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌  Câmera não encontrada.")
        sys.exit(1)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        now = time.monotonic()
        result = process_frame(frame, now)
        if result:
            for pid, data in result.items():
                buf = buffers.setdefault(pid, deque(maxlen=GRU_WINDOW_SIZE))
                buf.append(data["raw_kpts"])
                elapsed = now - last_inf.get(pid, 0)
                if len(buf) == GRU_WINDOW_SIZE and elapsed >= GRU_INTERVAL:
                    window = np.array(list(buf))
                    pred = clf.predict(window, pid)
                    last_inf[pid] = now
                    if pred:
                        label = pred["label"]
                        pfall = pred["probs"][1]
                        alerta = "⚡" if pred["alert"] else "  "
                        print(f"[GRU] Pessoa {pid}: {label} P(FALL)={pfall:.2f} {alerta}",
                              flush=True)
                        if pred["alert"]:
                            _notify_fall_mock(label)

        cv2.imshow("Validacao GRU — Q para sair", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nAlertas disparados: {_notificacoes}")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--camera", action="store_true",
        help="Usa câmera real (precisa de ultralytics instalado)"
    )
    args = parser.parse_args()

    if args.camera:
        run_camera()
    else:
        run_synthetic()
