"""Interface interativa para a Ana: menu -> contagem -> gravação -> resumo.

As teclas só chegam se a janela do OpenCV tiver foco (clicar nela uma vez).
Fechar com Esc no menu, nunca com Ctrl+C no meio de uma tomada.
"""

from __future__ import annotations

import time

import cv2

from vigia_lab import audio, hud
from vigia_lab.app import LabContext, record_take
from vigia_lab.menu import MenuState

WINDOW = "VIGIA LAB"

_KEYS = {
    13: "enter", 27: "esc", 9: "tab",
    2490368: "up", 2621440: "down", 2424832: "left", 2555904: "right",
    ord("m"): "m", ord("M"): "m", ord("x"): "x", ord("X"): "x", ord("r"): "r", ord("R"): "r",
}


def translate_key(code: int) -> str:
    """Código de cv2.waitKeyEx -> nome de tecla ('' se nenhuma/desconhecida)."""
    return _KEYS.get(code, "")


def _wait(ms: int) -> str:
    return translate_key(cv2.waitKeyEx(ms))


def run_ui(ctx: LabContext, args) -> int:
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW, hud.W, hud.H)
    menu = MenuState(ctx.scenarios)
    message = ""
    pending_repeat = None
    try:
        while True:
            scenario = pending_repeat
            pending_repeat = None
            if scenario is None:
                items = [(s.id, s.label, ctx.next_take(s.id)) for s in menu.visible]
                cv2.imshow(WINDOW, hud.draw_menu(items, menu.index, menu.only, message))
                action = menu.handle(_wait(50))
                if action == "quit":
                    return 0
                if action != "start":
                    continue
                scenario = menu.selected
            message = ""
            repeat = _take_once(ctx, args, scenario)
            if repeat == "stop":
                message = "Tomada abortada ou camera indisponivel."
            elif repeat == "repeat":
                pending_repeat = scenario
            elif repeat == "menu":
                message = f"Salvo: {scenario.id}"
            elif repeat == "next":
                pending_repeat = scenario            # Enter = próxima tomada do mesmo cenário
    finally:
        cv2.destroyAllWindows()


def _take_once(ctx: LabContext, args, scenario) -> str:
    """Devolve 'repeat' | 'next' | 'menu' | 'stop'."""
    state = {"marks": 0, "abort": False, "phase": None, "tick": -1, "t_rec": 0.0}
    ui_ms: list[float] = []
    take_no = ctx.next_take(scenario.id)
    fps_hist: list[float] = []
    outcome_choice = {"v": "next"}

    def on_frame(frame, phase, remaining, rec):
        t0 = time.perf_counter()
        if phase != state["phase"]:
            if phase == "recording":
                audio.beep_start()
            state["phase"] = phase
        if phase == "countdown":
            tick = int(remaining)
            if tick != state["tick"]:
                state["tick"] = tick
                audio.beep_tick()
        fps_hist.append(frame.t_mono)
        del fps_hist[:-15]
        fps_now = (len(fps_hist) - 1) / (fps_hist[-1] - fps_hist[0]) if len(fps_hist) > 2 and fps_hist[-1] > fps_hist[0] else 0.0
        t_rel = (frame.t_wall - rec.t0) if rec is not None and rec.frames else 0.0
        cards = hud.latest_by_model(rec.decisions, t_rel) if rec is not None else {}
        kps = [o.keypoints for o in frame.observations]
        flash_on = int(time.perf_counter() * 4) % 2 == 0
        canvas = hud.draw_live(
            frame.image, kps, phase, remaining, args.duration, scenario.id, scenario.label,
            take_no, fps_now, cards, state["marks"], flash_on,
        )
        cv2.imshow(WINDOW, canvas)
        key = _wait(1)
        if key == "m" and phase == "recording":
            state["marks"] += 1
        elif key in ("x", "esc"):
            state["abort"] = True
        ui_ms.append((time.perf_counter() - t0) * 1000.0)

    def on_result(color, reasons, q, _dir) -> bool:
        audio.beep_end()
        if state["abort"]:
            return False                      # tomada abortada: nada é registrado
        cv2.imshow(WINDOW, hud.draw_summary(color, reasons, q, scenario.id, take_no))
        while True:
            key = _wait(100)
            if key == "enter":
                outcome_choice["v"] = "next"
                return True
            if key == "esc":
                outcome_choice["v"] = "menu"
                return True
            if key == "r":
                outcome_choice["v"] = "repeat"
                return False

    try:
        result = record_take(
            ctx, scenario, source=int(args.source), replay=False, duration=args.duration,
            countdown=args.countdown, min_frames=args.min_frames, ids_mode=args.ids, save_video=not args.no_video,
            on_frame=on_frame, should_stop=lambda: state["abort"],
            pending_marks=lambda: state["marks"], on_result=on_result,
            extra_quality=lambda: {"ui_ms_mean": sum(ui_ms) / len(ui_ms) if ui_ms else 0.0},
        )
    except Exception as error:  # câmera caiu etc.: volta ao menu em vez de encerrar
        print(f"Falha na tomada: {error}")
        return "stop"
    if result is None or state["abort"]:
        return "stop"
    return outcome_choice["v"]
