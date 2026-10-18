"""Desenho da janela para a Ana (legível a 2-3 m). Só ASCII: as fontes do OpenCV
não têm acentos/cedilha."""

from __future__ import annotations

import cv2
import numpy as np

W, H = 1280, 720
VIDEO_W = 960
FONT = cv2.FONT_HERSHEY_SIMPLEX

BG = (24, 24, 24)
WHITE = (240, 240, 240)
GREY = (140, 140, 140)
RED = (60, 60, 230)
GREEN = (80, 200, 80)
YELLOW = (40, 200, 240)
VERDICT_COLOR = {"verde": GREEN, "amarelo": YELLOW, "vermelho": RED}

SKELETON = [
    (0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
]
MODEL_ORDER = [("gru34", "GRU 34"), ("gru37", "GRU 37"), ("math", "MATEMATICO")]
ALERT_FLASH_S = 1.5


def _text(img, s, org, scale=1.0, color=WHITE, thick=2) -> None:
    cv2.putText(img, s, org, FONT, scale, color, thick, cv2.LINE_AA)


def blank() -> np.ndarray:
    img = np.empty((H, W, 3), dtype=np.uint8)
    img[:] = BG
    return img


def latest_by_model(decisions: list[dict], t_now: float) -> dict[str, dict]:
    """Última decisão de cada modelo + se houve alerta nos últimos ALERT_FLASH_S."""
    out: dict[str, dict] = {}
    for d in decisions[-300:]:
        cur = out.setdefault(d["model"], {"label": "-", "extra": "", "flash": False})
        cur["label"] = d["label"]
        if d["prob_fall"] != "":
            cur["extra"] = f"p(queda) {float(d['prob_fall']):.2f}"
        elif d["score"] != "":
            cur["extra"] = f"score {float(d['score']):.2f}"
        if d["alert"] and t_now - d["t_rel"] <= ALERT_FLASH_S:
            cur["flash"] = True
    return out


def draw_skeletons(img: np.ndarray, keypoints: list[np.ndarray], scale: float) -> None:
    for kp in keypoints:
        pts = [(int(x * scale), int(y * scale), c) for x, y, c in kp[:17]]
        for a, b in SKELETON:
            if pts[a][2] >= 0.3 and pts[b][2] >= 0.3:
                cv2.line(img, pts[a][:2], pts[b][:2], GREEN, 3, cv2.LINE_AA)
        for x, y, c in pts:
            if c >= 0.3:
                cv2.circle(img, (x, y), 4, (0, 220, 255), -1, cv2.LINE_AA)


def _fit(image: np.ndarray, width: int, height: int) -> tuple[np.ndarray, float, int, int]:
    h, w = image.shape[:2]
    scale = min(width / w, height / h)
    resized = cv2.resize(image, (int(w * scale), int(h * scale)))
    return resized, scale, (width - resized.shape[1]) // 2, (height - resized.shape[0]) // 2


def draw_live(
    image: np.ndarray | None, keypoints: list[np.ndarray], phase: str, remaining: float,
    duration: float, scenario_id: str, label: str, take: int, fps_now: float,
    cards: dict[str, dict], marks: int, flash_on: bool,
) -> np.ndarray:
    canvas = blank()
    if image is not None:
        view, scale, ox, oy = _fit(image, VIDEO_W, H)
        raw_scale = scale
        draw_skeletons(view, keypoints, raw_scale)
        canvas[oy:oy + view.shape[0], ox:ox + view.shape[1]] = view

    color = RED if label == "FALL" else GREEN
    _text(canvas, f"{scenario_id}  take {take:02d}  [{label}]", (16, 36), 0.9, color)

    if phase == "countdown":
        _text(canvas, str(int(np.ceil(remaining))) if remaining > 0 else "JA", (VIDEO_W // 2 - 60, H // 2 + 60), 6.0, YELLOW, 12)
        _text(canvas, "PREPARAR", (VIDEO_W // 2 - 150, H // 2 - 120), 2.0, YELLOW, 4)
    else:
        if flash_on:
            cv2.circle(canvas, (36, 80), 14, RED, -1)
        _text(canvas, "REC", (60, 92), 1.1, RED, 3)
        frac = 1.0 - remaining / max(duration, 1e-6)
        cv2.rectangle(canvas, (16, H - 40), (VIDEO_W - 16, H - 16), GREY, 2)
        cv2.rectangle(canvas, (16, H - 40), (16 + int((VIDEO_W - 32) * frac), H - 16), RED, -1)
        _text(canvas, f"{remaining:4.1f}s", (VIDEO_W - 170, H - 54), 1.2, WHITE, 3)
        _text(canvas, "m = marcar queda   x = abortar", (16, H - 56), 0.8, GREY, 2)
        if marks:
            _text(canvas, f"marcas: {marks}", (VIDEO_W - 330, 36), 0.9, YELLOW, 2)

    # painel lateral: um cartão por modelo
    _text(canvas, f"{fps_now:4.1f} fps", (VIDEO_W + 20, 40), 1.0, WHITE, 2)
    for i, (key, name) in enumerate(MODEL_ORDER):
        top = 70 + i * 200
        c = cards.get(key, {"label": "-", "extra": "", "flash": False})
        alerting = c["flash"]
        border = RED if (alerting and flash_on) else GREY
        cv2.rectangle(canvas, (VIDEO_W + 10, top), (W - 10, top + 180), border, 4 if alerting else 2)
        _text(canvas, name, (VIDEO_W + 24, top + 40), 1.0, WHITE, 2)
        lab_color = RED if c["label"] in ("FALL", "SUSPECT") else GREEN
        _text(canvas, c["label"], (VIDEO_W + 24, top + 100), 1.5, lab_color if c["label"] != "-" else GREY, 3)
        _text(canvas, c["extra"], (VIDEO_W + 24, top + 150), 0.8, GREY, 2)
    return canvas


def draw_menu(items: list[tuple[str, str, int]], selected: int, only: str | None, message: str = "") -> np.ndarray:
    """items: (scenario_id, label, proximo_take)."""
    canvas = blank()
    _text(canvas, "VIGIA LAB - escolha o cenario", (30, 50), 1.2, WHITE, 3)
    filtro = {None: "todos", "FALL": "so quedas", "ADL": "so ADL"}[only]
    _text(canvas, f"filtro: {filtro}   [Tab] muda   [setas] navegam   [Enter] inicia   [Esc] sai", (30, 90), 0.7, GREY, 2)
    col_h = 12
    for i, (sid, label, nxt) in enumerate(items):
        col, row = divmod(i, col_h)
        x, y = 30 + col * 620, 150 + row * 44
        if i == selected:
            cv2.rectangle(canvas, (x - 10, y - 30), (x + 590, y + 10), (70, 70, 70), -1)
        _text(canvas, f"{sid}", (x, y), 0.9, RED if label == "FALL" else GREEN, 2)
        _text(canvas, f"take {nxt:02d}", (x + 450, y), 0.8, GREY, 2)
    if message:
        _text(canvas, message, (30, H - 30), 0.9, YELLOW, 2)
    _text(canvas, "Clique na janela para ela receber as teclas.", (30, H - 70), 0.7, GREY, 2)
    return canvas


def draw_summary(color: str, reasons: list[str], q: dict, scenario_id: str, take: int) -> np.ndarray:
    canvas = blank()
    vc = VERDICT_COLOR[color]
    cv2.circle(canvas, (130, 160), 90, vc, -1)
    _text(canvas, color.upper(), (270, 150), 2.4, vc, 6)
    _text(canvas, f"{scenario_id}  take {take:02d}", (270, 205), 1.0, WHITE, 2)
    y = 300
    for r in reasons[:5]:
        _text(canvas, f"- {r}", (60, y), 1.0, WHITE, 2)
        y += 50
    stats = (
        f"fps pose {q.get('pose_fps', 0):.1f} | entregues {q.get('delivered_fps', 0):.1f}/s | "
        f"tracks {q.get('n_tracks', 0)} | tronco {q.get('torso_valid_frac', 0):.0%}"
    )
    _text(canvas, stats, (60, H - 150), 0.9, GREY, 2)
    if q.get("bottleneck"):
        _text(canvas, f"gargalo: {q['bottleneck']} | CPU {q.get('cpu_pct_mean', 0):.0f}%", (60, H - 110), 0.8, GREY, 2)
    _text(canvas, "[Enter] salvar e proxima   [r] descartar e repetir   [Esc] salvar e voltar ao menu", (60, H - 70), 0.8, YELLOW, 2)
    return canvas
