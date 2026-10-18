"""Acumula os frames de UMA tomada e grava os arquivos em disco.

Sem câmera, YOLO ou janela: recebe `FrameRecord`s e decisões já prontas, o que
torna testável o que mais pode errar em silêncio (zero-fill de ausências,
ordem temporal, número de clipes por pessoa, colunas do CSV).

Saída (superconjunto do keypoint_extraction):
  por pessoa : <clip_id>.npy (T,17,3), _labels.npy, _t.npy
  por tomada : <take>_raw.npz, <take>_decisions.csv, <take>_meta.json
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from vigia_lab.takes import clip_id, take_id

TORSO_JOINTS = (5, 6, 11, 12)
MIN_KPT_CONF = 0.3          # igual a core.models.constants.MIN_KPT_CONF
LABEL_ADL, LABEL_FALL = 0, 2

DECISION_FIELDS = [
    "take", "frame_idx", "t_rel", "person_id", "model", "label", "alert",
    "prob_fall", "score", "latency_ms",
]


@dataclass
class FrameRecord:
    frame_idx: int
    t_wall: float
    t_mono: float
    person_ids: list[int]
    keypoints: list[np.ndarray]     # (17,3) crus, PRÉ-filtro, um por pessoa
    delivered: bool
    yolo_ms: float
    brightness: float
    n_filtered: int = 0
    reset_all: bool = False
    untracked: bool = False
    wait_ms: float = 0.0
    consumer_ms: float = 0.0
    cpu_pct: float = 0.0


@dataclass
class ClipFiles:
    clip_id: str
    person_idx: int
    n_frames: int
    px_path: Path
    lbl_path: Path
    t_path: Path


@dataclass
class TakeRecorder:
    frames: list[FrameRecord] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    marks: list[float] = field(default_factory=list)      # t_rel da tecla 'm'
    resets: list[dict[str, Any]] = field(default_factory=list)

    @property
    def t0(self) -> float:
        return self.frames[0].t_wall if self.frames else 0.0

    def add_frame(self, rec: FrameRecord) -> None:
        self.frames.append(rec)
        if rec.reset_all:
            self.resets.append({"frame_idx": rec.frame_idx, "t_rel": rec.t_wall - self.t0})

    def add_decisions(self, frame_idx: int, t_wall: float, model: str, items, latency_ms: float) -> None:
        for d in items:
            detail = d.detail or {}
            probs = detail.get("probs")
            self.decisions.append({
                "frame_idx": frame_idx,
                "t_rel": t_wall - self.t0,
                "person_id": d.person_id,
                "model": model,
                "label": d.label,
                "alert": int(bool(d.alert)),
                "prob_fall": probs[1] if probs else "",
                "score": detail.get("score", ""),
                "latency_ms": round(latency_ms, 3),
            })

    def mark_event(self, t_wall: float) -> None:
        self.marks.append(t_wall - self.t0)

    # ------------------------------------------------------------------ arrays
    def t_wall(self) -> np.ndarray:
        return np.array([f.t_wall for f in self.frames], dtype=np.float64)

    def wait_ms(self) -> np.ndarray:
        return np.array([f.wait_ms for f in self.frames], dtype=np.float64)

    def yolo_ms(self) -> np.ndarray:
        return np.array([f.yolo_ms for f in self.frames], dtype=np.float64)

    def consumer_ms(self) -> np.ndarray:
        return np.array([f.consumer_ms for f in self.frames], dtype=np.float64)

    def cpu_pct(self) -> np.ndarray:
        return np.array([f.cpu_pct for f in self.frames], dtype=np.float64)

    def t_rel(self) -> np.ndarray:
        return self.t_wall() - self.t0

    def _per_person(self) -> dict[int, np.ndarray]:
        """person_id -> (T,17,3) com conf<0.3 zerada e zeros onde ausente."""
        n = len(self.frames)
        out: dict[int, np.ndarray] = {}
        for i, f in enumerate(self.frames):
            for pid, kp in zip(f.person_ids, f.keypoints):
                if pid < 0:
                    continue                 # detecção sem ID ignorada (modo grace)
                arr = out.setdefault(pid, np.zeros((n, 17, 3), dtype=np.float32))
                k = np.asarray(kp, dtype=np.float32)[:17, :3].copy()
                k[k[:, 2] < MIN_KPT_CONF] = 0.0
                arr[i] = k
        return out

    @staticmethod
    def torso_ok(kp: np.ndarray) -> np.ndarray:
        return (kp[:, list(TORSO_JOINTS), 2] > 0).all(axis=1)

    def person_tracks(self, min_frames: int) -> list[tuple[int, np.ndarray]]:
        """Tracks com tronco válido em >= min_frames frames, por ordem de person_id."""
        tracks = [
            (pid, kp) for pid, kp in sorted(self._per_person().items())
            if int(self.torso_ok(kp).sum()) >= min_frames
        ]
        return tracks

    def torso_valid_any(self, min_frames: int) -> np.ndarray:
        """Por frame: alguma pessoa (de um track válido) com tronco completo."""
        n = len(self.frames)
        ok = np.zeros(n, dtype=bool)
        for _pid, kp in self.person_tracks(min_frames):
            ok |= self.torso_ok(kp)
        return ok

    def id_stats(self) -> dict[str, int]:
        """Quantas vezes o conjunto de IDs entregue aos modelos mudou (cada mudança faz o
        vigia apagar o histórico da pessoa) e quantos frames usaram o ID de reserva 0
        (o tracker do Ultralytics começa em 1; 0 = `boxes.id` ausente -> range(n))."""
        changes = fallback = 0
        prev: set[int] | None = None
        for f in self.frames:
            if 0 in f.person_ids:
                fallback += 1
            if not f.delivered:
                continue
            cur = {i for i in f.person_ids if i >= 0}
            if prev is not None and cur and prev and cur != prev:
                changes += 1
            if cur:
                prev = cur
        untracked = sum(1 for f in self.frames if f.untracked)
        return {
            "id_set_changes_delivered": changes,
            "id_fallback_frames": fallback,
            "untracked_frames": untracked,
        }

    # ------------------------------------------------------------------ gravação
    def save_clips(
        self, out_dir: Path, scenario_id: str, take: int, is_fall: bool, min_frames: int,
    ) -> list[ClipFiles]:
        out_dir.mkdir(parents=True, exist_ok=True)
        label = LABEL_FALL if is_fall else LABEL_ADL
        rel_t = self.t_rel()
        clips: list[ClipFiles] = []
        for idx, (_pid, kp) in enumerate(self.person_tracks(min_frames)):
            cid = clip_id(scenario_id, take, idx)
            px, lbl, tp = out_dir / f"{cid}.npy", out_dir / f"{cid}_labels.npy", out_dir / f"{cid}_t.npy"
            np.save(px, kp)
            np.save(lbl, np.full(len(self.frames), label, dtype=np.int8))
            np.save(tp, rel_t)
            clips.append(ClipFiles(cid, idx, len(self.frames), px, lbl, tp))
        return clips

    def save_raw(self, path: Path) -> None:
        n = len(self.frames)
        max_p = max((len(f.person_ids) for f in self.frames), default=0)
        kp = np.zeros((n, max_p, 17, 3), dtype=np.float32)
        ids = np.full((n, max_p), -1, dtype=np.int64)
        for i, f in enumerate(self.frames):
            for j, (pid, k) in enumerate(zip(f.person_ids, f.keypoints)):
                ids[i, j] = pid
                kp[i, j] = np.asarray(k, dtype=np.float32)[:17, :3]
        np.savez_compressed(
            path,
            frame_idx=np.array([f.frame_idx for f in self.frames], dtype=np.int64),
            t_wall=self.t_wall(),
            t_mono=np.array([f.t_mono for f in self.frames], dtype=np.float64),
            delivered=np.array([f.delivered for f in self.frames], dtype=bool),
            untracked=np.array([f.untracked for f in self.frames], dtype=bool),
            yolo_ms=np.array([f.yolo_ms for f in self.frames], dtype=np.float32),
            wait_ms=self.wait_ms().astype(np.float32),
            consumer_ms=self.consumer_ms().astype(np.float32),
            cpu_pct=self.cpu_pct().astype(np.float32),
            brightness=np.array([f.brightness for f in self.frames], dtype=np.float32),
            person_ids=ids,
            keypoints=kp,
        )

    def save_decisions(self, path: Path, take_name: str) -> None:
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=DECISION_FIELDS)
            w.writeheader()
            for row in self.decisions:
                w.writerow({"take": take_name, **row})

    def save_meta(self, path: Path, meta: dict[str, Any]) -> None:
        meta = {**meta, "marks_t_rel": self.marks, "resets": self.resets}
        path.write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")


def _json_default(o: Any) -> Any:
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f"não serializável: {type(o)}")


def take_paths(captures_dir: Path, scenario_id: str, take: int) -> dict[str, Path]:
    d = captures_dir / scenario_id
    name = take_id(scenario_id, take)
    return {
        "dir": d,
        "raw": d / f"{name}_raw.npz",
        "decisions": d / f"{name}_decisions.csv",
        "meta": d / f"{name}_meta.json",
        "video": d / f"{name}.avi",
    }
