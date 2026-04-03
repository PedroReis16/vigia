"""Parse de endereço TCP de ingest (4 bytes LE + JPEG), compatível com URLs ws/http."""

from __future__ import annotations

import os


def parse_tcp_ingest_addr(raw: str) -> tuple[str, int] | None:
    """
    Destino do socket TCP do vigia-stream (4 bytes LE + JPEG), não HTTP/WebSocket.
    Aceita host:porta, URLs com path (/stream é ignorado) e ws(s):// (só host/porta).
    """
    s = raw.strip()
    if not s:
        return None
    lower = s.lower()
    for prefix in ("tcp://", "http://", "https://", "ws://", "wss://"):
        if lower.startswith(prefix):
            s = s[len(prefix) :]
            break
    if "/" in s:
        s = s.split("/", 1)[0]
    if ":" in s:
        host, _, port_s = s.rpartition(":")
        host = host.strip()
        if not host:
            return None
        try:
            port = int(port_s)
        except ValueError:
            return None
    else:
        host, port = s, 8090
    # Em docker local, ws://…:8091 é o Gin; o ingest TCP da câmera no Go é :8090
    if port == 8091:
        port = 8090
    return (host, port)


def tcp_stream_target_from_env() -> tuple[str, int] | None:
    for key in ("STREAM_TCP_ADDR", "STREAM_WS_URL"):
        raw = (os.getenv(key) or "").strip()
        if not raw:
            continue
        t = parse_tcp_ingest_addr(raw)
        if t:
            return t
    return None
