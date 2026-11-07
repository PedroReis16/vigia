"""Política de IDs ativos para o cleanup (correção do histórico apagado por troca de ID).

No vigia, `cleanup(active_ids)` apaga o estado de quem não está no frame ENTREGUE
(amostrado). Se o tracker do Ultralytics devolve zero tracks num frame
(`on_predict_postprocess_end: if len(tracks)==0: continue`), as caixas ficam sem
`boxes.id`, o `unpack_raw_points` numera 0..n-1 e a pessoa 1 vira 0: o histórico
dela é apagado e a janela leva 2-3 s para encher de novo.

`IdGrace` mantém como "ativo" quem foi visto nos últimos `grace_s` segundos.
"""

from __future__ import annotations

DEFAULT_GRACE_S = 1.5
MODES = ("baseline", "grace")


class IdGrace:
    def __init__(self, grace_s: float = DEFAULT_GRACE_S) -> None:
        self._grace = grace_s
        self._last_seen: dict[int, float] = {}

    def active(self, batch_ids: set[int], now: float) -> set[int]:
        for pid in batch_ids:
            self._last_seen[pid] = now
        expired = [p for p, t in self._last_seen.items() if now - t > self._grace]
        for pid in expired:
            del self._last_seen[pid]
        return set(self._last_seen)
