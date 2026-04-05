"""Fábrica de `StreamOutWorker` a partir de URL HTTP ou host/porta TCP."""

from __future__ import annotations

from app.capture.io.stream_out_worker import StreamOutWorker


def optional_stream_worker(
    stream_ingest_url: str,
    stream_ingest_token: str,
    stream_target: tuple[str, int] | None,
) -> StreamOutWorker | None:
    """Cria e inicia worker de saída conforme URL HTTP ou alvo TCP."""
    w = StreamOutWorker()
    if stream_ingest_url:
        w.start_http(stream_ingest_url, stream_ingest_token)
        return w
    if stream_target:
        w.start_tcp(stream_target[0], stream_target[1])
        return w
    return None
