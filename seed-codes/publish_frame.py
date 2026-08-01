"""
Seed local: publica um frame JPEG em POST /vigia/devices/{deviceId}/frame
com autenticação DeviceSignature (Ed25519).

Deps: pip install -r requirements.txt

Par de chaves alinhado com TestDeviceSeed (DEBUG). Reinicie a API para
sincronizar SignPublicKey no banco se ainda estiver o placeholder antigo.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from pathlib import Path

import requests
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

# --- config (espelha Vigia.Models.Seed.TestDeviceSeed) ---
BASE_URL = "http://localhost:8090/vigia"
DEVICE_ID = "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"
# Raw private seed (32 bytes hex) — NÃO é a SignPublicKey do banco
SIGN_PRIVATE_KEY_HEX = "a1b2c3d4e5f60718293a4b5c6d7e8f90112233445566778899aabbccddeeff00"
# Pública correspondente (deve bater com Devices.sign_public_key):
# 42aaead72ceea9f9423f281440c6cfac7a5f99b796b81862f452328972b21b61
FRAME_PATH = Path(__file__).parent / "assets" / "frame.jpg"

_MIN_JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000"
    "ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432"
    "ffdb0043010909090c0b0c180d0d1832211c213232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232"
    "ffc00011080001000103011100021100031100"
    "ffc40014000100000000000000000000000000000000"
    "ffc40014100100000000000000000000000000000000"
    "ffda000c0301000210031000003f00bf80"
    "ffd9"
)


def _load_signing_key() -> Ed25519PrivateKey:
    priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(SIGN_PRIVATE_KEY_HEX))
    pub_hex = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
    print(f"SignPublicKey esperada no banco: {pub_hex}")
    return priv


def _jpeg_bytes() -> bytes:
    if FRAME_PATH.is_file():
        return FRAME_PATH.read_bytes()
    return _MIN_JPEG


def _build_multipart(jpeg: bytes, field_name: str = "frameFile") -> tuple[bytes, str]:
    boundary = f"----VigiaBoundary{uuid.uuid4().hex}"
    filename = FRAME_PATH.name if FRAME_PATH.is_file() else "frame.jpg"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                f"Content-Type: image/jpeg\r\n\r\n"
            ).encode(),
            jpeg,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return body, f"multipart/form-data; boundary={boundary}"


def publish_frame() -> None:
    device_id = uuid.UUID(DEVICE_ID)
    priv = _load_signing_key()
    body, content_type = _build_multipart(_jpeg_bytes())

    timestamp = int(time.time())
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = f"POST\n/devices/{device_id}/frame\n{timestamp}\n{body_hash}"
    signature_hex = priv.sign(canonical.encode("utf-8")).hex()

    url = f"{BASE_URL}/devices/{device_id}/frame"
    resp = requests.post(
        url,
        data=body,
        headers={
            "Content-Type": content_type,
            "X-Device-Timestamp": str(timestamp),
            "X-Device-Signature": signature_hex,
        },
        timeout=30,
    )
    print(f"{resp.status_code} {resp.reason}")
    if resp.content:
        print(resp.text)


if __name__ == "__main__":
    publish_frame()
