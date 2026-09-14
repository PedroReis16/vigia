"""
Espelha Vigia.Models.Seed.TestDeviceSeed (API DEBUG).

Em DEBUG, MigrationStartupFilter força SignPublicKey deste par no device
seedado. identity.json local que use o mesmo device_id precisa da mesma
chave privada derivada — senão POST /devices/{id}/frame retorna 401.

A private key NÃO é versionada: deriva de SHA-256("vigia-debug-test-device-v1").
"""

from __future__ import annotations

import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

# Guid do device seedado na API (TestDeviceSeed.Id)
DEVICE_ID = "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"

_DEBUG_SEED_PASSPHRASE = b"vigia-debug-test-device-v1"


def _derive_sign_private_key_hex() -> str:
    return hashlib.sha256(_DEBUG_SEED_PASSPHRASE).hexdigest()


def _derive_sign_public_key_hex(private_key_hex: str) -> str:
    priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
    return priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()


# Ed25519 raw private seed (hex) — alinhado ao TestDeviceSeed.SignPublicKey
SIGN_PRIVATE_KEY = _derive_sign_private_key_hex()

# Ed25519 raw public key (hex) — TestDeviceSeed.SignPublicKey
SIGN_PUBLIC_KEY = _derive_sign_public_key_hex(SIGN_PRIVATE_KEY)
