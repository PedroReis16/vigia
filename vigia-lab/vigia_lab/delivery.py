"""Entrega de um lote aos classificadores, na ordem exata do FrameWorker._handle.

    active_ids (lote BRUTO) -> filter_observations -> process (cada modelo)
    -> PersonRuntimeStore.cleanup -> cleanup (cada modelo)

Lote vazio (ninguém detectado) TAMBÉM é entregue: no vigia isso chama
cleanup(set()) e zera janelas/Kalman. O lab reproduz e registra o evento.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from core.models.types import FallDecision, PoseObservation


@dataclass
class DeliveryResult:
    decisions: dict[str, list[FallDecision]] = field(default_factory=dict)
    latency_ms: dict[str, float] = field(default_factory=dict)
    n_filtered: int = 0
    reset_all: bool = False  # lote vazio: histórico de todos foi apagado


def deliver_batch(
    batch: list[PoseObservation],
    classifiers: Mapping[str, Any],
    filter_fn: Callable[[list[PoseObservation]], list[PoseObservation]],
    runtime_store_fn: Callable[[], Any],
    active_ids_fn: Callable[[set[int]], set[int]] | None = None,
) -> DeliveryResult:
    """`active_ids_fn` (opcional) substitui os IDs do lote pelos IDs a preservar no
    cleanup (ex.: `IdGrace.active`); sem ele vale o comportamento do vigia."""
    batch_ids = {obs.person_id for obs in batch}
    active_ids = active_ids_fn(batch_ids) if active_ids_fn else batch_ids
    filtered = filter_fn(batch)
    result = DeliveryResult(n_filtered=len(filtered), reset_all=not active_ids)

    for name, classifier in classifiers.items():
        t0 = time.perf_counter()
        result.decisions[name] = classifier.process(filtered)
        result.latency_ms[name] = (time.perf_counter() - t0) * 1000.0

    runtime_store_fn().cleanup(active_ids)
    for classifier in classifiers.values():
        cleanup = getattr(classifier, "cleanup", None)
        if cleanup is not None:
            cleanup(active_ids)
    return result
