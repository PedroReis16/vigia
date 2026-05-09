"""Codificação binária de frames (numpy) para ZMQ — alternativa segura ao pickle no IPC local."""

from __future__ import annotations

import json
import struct
from typing import Any

import numpy as np

_MAGIC = b"VGF1"
_MAX_META_LEN = 4096


def encode_numpy_frame(frame: np.ndarray) -> bytes:
    """Serializa um ndarray contíguo em bytes (shape/dtype + payload bruto)."""
    arr = np.ascontiguousarray(frame)
    meta: dict[str, Any] = {"shape": arr.shape, "dtype": arr.dtype.str}
    meta_bytes = json.dumps(meta, separators=(",", ":")).encode("utf-8")
    if len(meta_bytes) > _MAX_META_LEN:
        raise ValueError("frame metadata too large")
    return _MAGIC + struct.pack("<I", len(meta_bytes)) + meta_bytes + arr.tobytes()


def decode_numpy_frame(payload: bytes) -> np.ndarray:
    """Reconstrói ndarray a partir do formato produzido por ``encode_numpy_frame``."""
    min_header = len(_MAGIC) + 4
    if len(payload) < min_header or payload[: len(_MAGIC)] != _MAGIC:
        raise ValueError("invalid frame payload (magic)")
    (meta_len,) = struct.unpack("<I", payload[len(_MAGIC) : min_header])
    if meta_len > _MAX_META_LEN:
        raise ValueError("invalid frame metadata length")
    meta_end = min_header + meta_len
    if len(payload) < meta_end:
        raise ValueError("truncated frame metadata")
    meta = json.loads(payload[min_header:meta_end].decode("utf-8"))
    raw = payload[meta_end:]
    dtype = np.dtype(meta["dtype"])
    expected = int(np.prod(meta["shape"], dtype=np.int64)) * dtype.itemsize
    if len(raw) != expected:
        raise ValueError("frame byte length does not match shape/dtype")
    out = np.frombuffer(raw, dtype=dtype).reshape(meta["shape"])
    return np.array(out, copy=True)
