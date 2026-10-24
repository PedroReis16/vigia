"""Gravador leve para a Ana: escolhe o clipe, grava vídeo a ~30 fps e marca o início/fim da queda.

Sem esqueleto e sem modelos durante a gravação (a análise é offline). Depois de cada tomada roda a
verificação rápida de pose (~1 s) e mostra o semáforo da CAPTURA. Textos só em ASCII (fontes do OpenCV).

Teclas  menu: setas/Tab/Enter, d = duracao fixa/manual, Esc = sair
        gravando: m = inicio da queda, n = fim (contato com o chao), u = desfaz, x = aborta,
                  Espaco/Enter = encerra (modo manual)
        resumo: Enter = salvar e proxima, r = descartar e repetir, Esc = salvar e menu
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from vigia_lab import audio, hud
from vigia_lab.app import LabContext, fingerprint_for
from vigia_lab.capture_quality import capture_metrics, capture_verdict
from vigia_lab.lite_capture import DEFAULT_FPS, DEFAULT_RESOLUTION, LiteCamera
from vigia_lab.marks import DurationPolicy, EventMarks
from vigia_lab.menu import MenuState
from vigia_lab.quick_check import run_quick_check
from vigia_lab.recordings import Recording, append_recording, takes_recorded
from vigia_lab.recorder import take_paths
from vigia_lab.sidecar import save_capture_meta, save_frames, sidecar_paths
from vigia_lab.takes import next_take_number, take_id, takes_from_videos
from vigia_lab.ui import _KEYS as _BASE_KEYS

WINDOW = "VIGIA LAB - GRAVADOR"
_KEYS = {**_BASE_KEYS, ord("n"): "n", ord("N"): "n", ord("u"): "u", ord("U"): "u", ord("d"): "d",
         ord("D"): "d", 32: "space"}
PREVIEW_PERIOD_S = 1 / 15
COUNTDOWN_S = 3.0
VERDICT_COLOR = hud.VERDICT_COLOR


def _key(ms: int) -> str:
    return _KEYS.get(cv2.waitKeyEx(ms), "")


def parse_resolution(text: str) -> tuple[int, int]:
    w, h = text.lower().split("x")
    return int(w), int(h)


# ------------------------------------------------------------------ desenho
def _preview(frame: np.ndarray | None) -> np.ndarray:
    canvas = hud.blank()
    if frame is not None:
        view, _scale, ox, oy = hud._fit(frame, hud.VIDEO_W, hud.H)
        canvas[oy:oy + view.shape[0], ox:ox + view.shape[1]] = view
    return canvas


def draw_countdown(frame, scenario, take_no, remaining: float, live_fps: float) -> np.ndarray:
    c = _preview(frame)
    hud._text(c, f"{scenario.id}  take {take_no:02d}  [{scenario.label}]", (16, 36), 0.9,
              hud.RED if scenario.is_fall else hud.GREEN)
    hud._text(c, "PREPARAR", (hud.VIDEO_W // 2 - 150, hud.H // 2 - 120), 2.0, hud.YELLOW, 4)
    hud._text(c, str(max(int(np.ceil(remaining)), 1)), (hud.VIDEO_W // 2 - 60, hud.H // 2 + 60), 6.0, hud.YELLOW, 12)
    hud._text(c, f"camera {live_fps:4.1f} fps", (hud.VIDEO_W + 20, 40), 1.0,
              hud.RED if live_fps < 20 else hud.WHITE, 2)
    return c


def draw_recording(frame, scenario, take_no, elapsed, policy: DurationPolicy, marks: EventMarks,
                   live_fps: float, flash_on: bool) -> np.ndarray:
    c = _preview(frame)
    hud._text(c, f"{scenario.id}  take {take_no:02d}  [{scenario.label}]", (16, 36), 0.9,
              hud.RED if scenario.is_fall else hud.GREEN)
    if flash_on:
        cv2.circle(c, (36, 80), 14, hud.RED, -1)
    hud._text(c, "REC", (60, 92), 1.1, hud.RED, 3)
    remaining = policy.remaining(elapsed)
    if remaining is not None:
        frac = 1.0 - remaining / max(policy.fixed_s, 1e-6)
        cv2.rectangle(c, (16, hud.H - 40), (hud.VIDEO_W - 16, hud.H - 16), hud.GREY, 2)
        cv2.rectangle(c, (16, hud.H - 40), (16 + int((hud.VIDEO_W - 32) * frac), hud.H - 16), hud.RED, -1)
        hud._text(c, f"{remaining:4.1f}s", (hud.VIDEO_W - 170, hud.H - 54), 1.2, hud.WHITE, 3)
    else:
        hud._text(c, f"{elapsed:5.1f}s  (Espaco encerra)", (hud.VIDEO_W - 420, hud.H - 24), 1.0, hud.WHITE, 2)
    hud._text(c, f"camera {live_fps:4.1f} fps", (hud.VIDEO_W + 20, 40), 1.0,
              hud.RED if live_fps < 20 else hud.WHITE, 2)
    y = 120
    for label, value, key in (("INICIO da queda", marks.start_t, "m"), ("FIM (no chao)", marks.end_t, "n")):
        done = value is not None
        hud._text(c, f"[{key}] {label}", (hud.VIDEO_W + 20, y), 0.8, hud.GREEN if done else hud.GREY, 2)
        hud._text(c, f"{value:5.1f}s" if done else "--", (hud.VIDEO_W + 20, y + 40), 1.1,
                  hud.GREEN if done else hud.GREY, 2)
        y += 110
    hud._text(c, "[u] desfaz   [x] aborta", (hud.VIDEO_W + 20, hud.H - 24), 0.7, hud.GREY, 2)
    return c


def draw_message(text: str, sub: str = "") -> np.ndarray:
    c = hud.blank()
    hud._text(c, text, (60, hud.H // 2), 1.4, hud.YELLOW, 3)
    if sub:
        hud._text(c, sub, (60, hud.H // 2 + 60), 0.9, hud.GREY, 2)
    return c


def draw_summary(color: str, reasons: list[str], metrics: dict, pose: dict, marks: EventMarks,
                 scenario_id: str, take_no: int) -> np.ndarray:
    c = hud.blank()
    vc = VERDICT_COLOR[color]
    cv2.circle(c, (130, 160), 90, vc, -1)
    hud._text(c, color.upper(), (270, 150), 2.4, vc, 6)
    hud._text(c, f"{scenario_id}  take {take_no:02d}", (270, 205), 1.0, hud.WHITE, 2)
    y = 300
    for r in reasons[:5]:
        hud._text(c, f"- {r}", (60, y), 1.0, hud.WHITE, 2)
        y += 50
    stats = (f"camera {metrics.get('measured_fps', 0):.1f} fps | {metrics.get('n_frames', 0)} frames | "
             f"perdidos {metrics.get('dropped_frames', 0)} | tronco {pose.get('torso_valid_frac', 0):.0%}")
    hud._text(c, stats, (60, hud.H - 170), 0.9, hud.GREY, 2)
    mk = f"marcas: inicio {marks.start_t if marks.start_t is not None else '--'}  fim {marks.end_t if marks.end_t is not None else '--'}"
    hud._text(c, mk, (60, hud.H - 125), 0.9, hud.GREY, 2)
    hud._text(c, "[Enter] salvar e proxima   [r] descartar e repetir   [Esc] salvar e voltar ao menu",
              (60, hud.H - 60), 0.8, hud.YELLOW, 2)
    return c


# ------------------------------------------------------------------ fluxo
def _next_take(ctx: LabContext, scenario_id: str) -> int:
    return next_take_number(
        takes_recorded(ctx.out / "recordings.csv", scenario_id)
        | takes_from_videos(ctx.out / scenario_id, scenario_id)
    )


def run_recorder(ctx: LabContext, args) -> int:
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW, hud.W, hud.H)
    menu = MenuState(ctx.scenarios)
    policy = DurationPolicy("fixed", args.duration)
    message = ""
    pending: Any = None
    try:
        while True:
            scenario, pending = pending, None
            if scenario is None:
                items = [(s.id, s.label, _next_take(ctx, s.id)) for s in menu.visible]
                mode = f"FIXA {policy.fixed_s:.0f} s" if policy.mode == "fixed" else "MANUAL (a Ana encerra)"
                cv2.imshow(WINDOW, hud.draw_menu(items, menu.index, menu.only, f"[d] duracao: {mode}   {message}"))
                key = _wait_menu()
                if key == "d":
                    policy = policy.toggled()
                    continue
                action = menu.handle(key)
                if action == "quit":
                    return 0
                if action != "start":
                    continue
                scenario = menu.selected
            message = ""
            outcome = _record_one(ctx, args, scenario, policy)
            if outcome == "stop":
                message = "Tomada abortada ou camera indisponivel."
            elif outcome in ("repeat", "next"):
                pending = scenario
            elif outcome == "menu":
                message = f"Salvo: {scenario.id}"
    finally:
        cv2.destroyAllWindows()


def _wait_menu() -> str:
    return _key(50)


def _record_one(ctx: LabContext, args, scenario, policy: DurationPolicy) -> str:
    take_no = _next_take(ctx, scenario.id)
    resolution = parse_resolution(args.resolution)
    cam = LiteCamera(args.source, resolution, args.fps)
    cv2.imshow(WINDOW, draw_message("Abrindo a camera..."))
    cv2.waitKey(1)
    if not cam.open():
        cv2.imshow(WINDOW, draw_message("Camera nao abriu", "Feche outros programas que usam a camera."))
        cv2.waitKey(1500)
        return "stop"
    try:
        deadline = time.time() + 5
        while cam.latest() is None and cam.error is None and time.time() < deadline:
            time.sleep(0.01)
        if cam.latest() is None:
            return "stop"

        # contagem regressiva sobre a imagem ao vivo (também estabiliza a exposição)
        t_end, last_tick = time.monotonic() + COUNTDOWN_S, -1
        while True:
            remaining = t_end - time.monotonic()
            if remaining <= 0:
                break
            tick = int(np.ceil(remaining))
            if tick != last_tick:
                last_tick = tick
                audio.beep_tick()
            snap = cam.latest()
            cv2.imshow(WINDOW, draw_countdown(snap[0] if snap else None, scenario, take_no, remaining, cam.live_fps()))
            if _key(15) in ("x", "esc") or cam.error:
                return "stop"

        paths = take_paths(ctx.out, scenario.id, take_no)
        cam.begin_recording(paths["video"])
        audio.beep_start()
        marks, stop_requested, aborted = EventMarks(), False, False
        last_draw = 0.0
        while not policy.finished(cam.recorded_seconds(), stop_requested):
            if cam.error:
                aborted = True
                break
            now = time.monotonic()
            t0 = cam.recording_t0()
            t_rel = (now - t0) if t0 is not None else 0.0
            key = _key(5)
            if key == "m":
                marks.press_start(t_rel)
            elif key == "n":
                marks.press_end(t_rel)
            elif key == "u":
                marks.undo()
            elif key in ("x", "esc"):
                aborted = True
                break
            elif key in ("space", "enter") and policy.mode == "manual":
                stop_requested = True
            if now - last_draw >= PREVIEW_PERIOD_S:
                last_draw = now
                snap = cam.latest()
                cv2.imshow(WINDOW, draw_recording(
                    snap[0] if snap else None, scenario, take_no, cam.recorded_seconds(), policy, marks,
                    cam.live_fps(), int(now * 4) % 2 == 0))
        audio.beep_end()
        result = cam.end_recording()
    finally:
        cam.close()

    if aborted:
        _delete_take(paths)
        return "stop"
    return _finish_take(ctx, args, scenario, take_no, policy, marks, result, paths)


def _finish_take(ctx, args, scenario, take_no, policy, marks, result, paths) -> str:
    cv2.imshow(WINDOW, draw_message("Verificando a gravacao...", "Rodando o detector em alguns quadros (~1 s)"))
    cv2.waitKey(1)
    metrics = capture_metrics(result.clock.t_mono, result.clock.brightness, result.dropped, result.nominal_fps)
    pose = run_quick_check(ctx, result.video_path)
    color, reasons = capture_verdict(metrics, pose)

    side = sidecar_paths(result.video_path)
    save_frames(side["frames"], result.clock)
    save_capture_meta(side["capture"], {
        "take": take_id(scenario.id, take_no), "scenario_id": scenario.id, "scenario_label": scenario.label,
        "take_number": take_no, "session_id": ctx.session_id, "video_path": result.video_path,
        "nominal_fps": result.nominal_fps, "resolution": result.resolution,
        "duration_mode": policy.mode, "duration_fixed_s": policy.fixed_s,
        "marks": marks.as_dict(),
        "capture_metrics": metrics, "pose_check": pose,
        "capture_quality": {"verdict": color, "reasons": reasons},
        "fingerprint": fingerprint_for(ctx),
    })

    cv2.imshow(WINDOW, draw_summary(color, reasons, metrics, pose, marks, scenario.id, take_no))
    while True:
        key = _key(100)
        if key in ("enter", "esc"):
            append_recording(ctx.out / "recordings.csv", Recording(
                take_id=take_id(scenario.id, take_no), scenario_id=scenario.id, scenario_label=scenario.label,
                take_number=take_no, session_id=ctx.session_id, video_path=result.video_path,
                frames_path=side["frames"], capture_path=side["capture"], n_frames=metrics["n_frames"],
                duration_s=metrics.get("duration_s", 0.0), measured_fps=round(metrics["measured_fps"], 2),
                capture_verdict=color, event_start_t=marks.start_t, event_end_t=marks.end_t,
                duration_mode=policy.mode,
            ))
            return "next" if key == "enter" else "menu"
        if key == "r":
            _delete_take(paths)
            return "repeat"


def _delete_take(paths: dict[str, Path]) -> None:
    video = paths["video"]
    side = sidecar_paths(video)
    for p in (video, side["frames"], side["capture"]):
        p.unlink(missing_ok=True)
