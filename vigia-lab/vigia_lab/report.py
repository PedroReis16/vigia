"""Métricas por clipe × configuração e tabela resumo (CSV + Markdown).

Definições (explicação para o PFC):
- Início de referência da queda = `event_t_auto` (ângulo do tronco > 60° por 2 frames); se não existir,
  a marca da operadora menos 0,4 s (a marca feita por outra pessoa sai ~0,4 s depois do início real).
- Clipe de QUEDA é "detectado" se o modelo emite `alert` em [início, fim + 2 s] (fim = marca `n`;
  sem fim, início + 5 s). O 2 s extra cobre a confirmação temporal (2 predições seguidas dos GRUs).
  Latência = 1º alerta na janela − início de referência. Alerta antes do início é contado à parte.
- Clipe ADL tem "falso alarme" se houver QUALQUER `alert` no clipe.
- Maior intervalo sem decisão mede o efeito de histórico apagado (troca de ID) e de janelas enchendo.
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

MODELS = ("gru34", "gru37", "math")
DEFAULT_REACTION_S = 0.4
POST_END_S = 2.0
NO_END_WINDOW_S = 5.0


def reference_start(meta: dict[str, Any]) -> float | None:
    auto = meta.get("event_t_auto")
    if auto is not None:
        return float(auto)
    mark = meta.get("event_start_t")
    return float(mark) - DEFAULT_REACTION_S if mark is not None else None


def evaluate_take(meta: dict[str, Any], decisions: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Uma linha por modelo."""
    is_fall = meta["scenario_label"] == "FALL"
    start = reference_start(meta)
    end = meta.get("event_end_t")
    q = meta["quality"]
    rows = []
    for model in MODELS:
        mine = [d for d in decisions if d["model"] == model]
        times = [float(d["t_rel"]) for d in mine]
        alerts = [float(d["t_rel"]) for d in mine if d["alert"] == "1"]
        gap = max((b - a for a, b in zip(times, times[1:])), default=None)
        row: dict[str, Any] = {
            "take": meta["take"], "tag": meta.get("tag", ""), "model": model, "label": meta["scenario_label"],
            "n_decisions": len(mine), "n_alerts": len(alerts),
            "max_gap_s": round(gap, 2) if gap is not None else "",
            "delivered_fps": round(q.get("delivered_fps", 0.0), 2),
            "untracked_frames": q.get("untracked_frames", 0),
            "id_changes": q.get("id_set_changes_delivered", 0),
            "resets": len(meta.get("resets", [])),
            "detected": "", "latency_s": "", "alert_before_start": "", "false_alarm": "",
        }
        if is_fall:
            if start is None:
                row["detected"] = int(bool(alerts))
            else:
                window_end = (float(end) if end is not None else start + NO_END_WINDOW_S - POST_END_S) + POST_END_S
                inside = [t for t in alerts if start <= t <= window_end]
                row["detected"] = int(bool(inside))
                row["latency_s"] = round(inside[0] - start, 2) if inside else ""
                row["alert_before_start"] = int(any(t < start for t in alerts))
        else:
            row["false_alarm"] = int(bool(alerts))
        rows.append(row)
    return rows


def collect(root: Path) -> list[dict[str, Any]]:
    """Lê `root/<tag>/<cenário>/<take>_meta.json` + `_decisions.csv`."""
    rows: list[dict[str, Any]] = []
    for meta_path in sorted(root.glob("*/*/*_meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        dec_path = meta_path.with_name(meta_path.name.replace("_meta.json", "_decisions.csv"))
        with dec_path.open(encoding="utf-8", newline="") as fh:
            decisions = list(csv.DictReader(fh))
        meta.setdefault("tag", meta_path.parent.parent.name)
        rows.extend(evaluate_take(meta, decisions))
    return rows


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Uma linha por (tag, modelo): detecção e latência em quedas, falso alarme em ADL."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["tag"], r["model"])].append(r)
    out = []
    for (tag, model), rs in sorted(groups.items()):
        falls = [r for r in rs if r["label"] == "FALL"]
        adls = [r for r in rs if r["label"] == "ADL"]
        lat = [float(r["latency_s"]) for r in falls if r["latency_s"] != ""]
        out.append({
            "tag": tag, "model": model,
            "falls": len(falls), "detected": sum(int(r["detected"] or 0) for r in falls),
            "median_latency_s": round(statistics.median(lat), 2) if lat else "",
            "adl": len(adls), "false_alarms": sum(int(r["false_alarm"] or 0) for r in adls),
            "max_gap_s": max((float(r["max_gap_s"]) for r in rs if r["max_gap_s"] != ""), default=""),
            "id_changes": sum(int(r["id_changes"]) for r in rs) // 1,
        })
    return out


def to_markdown(summary: list[dict[str, Any]]) -> str:
    head = "| Configuração | Modelo | Quedas detectadas | Latência mediana (s) | ADL com falso alarme | Maior intervalo sem decisão (s) | Trocas de ID |\n"
    sep = "|---|---|---|---|---|---|---|\n"
    lines = []
    for s in summary:
        lines.append(
            f"| {s['tag']} | {s['model']} | {s['detected']}/{s['falls']} | {s['median_latency_s']} | "
            f"{s['false_alarms']}/{s['adl']} | {s['max_gap_s']} | {s['id_changes']} |"
        )
    return head + sep + "\n".join(lines) + "\n"


def write_outputs(root: Path) -> tuple[Path, Path, Path]:
    rows = collect(root)
    summary = summarize(rows)
    per_take = root / "report_por_clipe.csv"
    if rows:
        with per_take.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    summ_csv, summ_md = root / "report_resumo.csv", root / "report_resumo.md"
    if summary:
        with summ_csv.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(summary[0]))
            w.writeheader()
            w.writerows(summary)
    summ_md.write_text(to_markdown(summary), encoding="utf-8")
    return per_take, summ_csv, summ_md
