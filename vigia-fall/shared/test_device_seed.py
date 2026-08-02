"""
Espelha Vigia.Models.Seed.TestDeviceSeed (API DEBUG).

Em DEBUG, MigrationStartupFilter força SignPublicKey deste par no device
seedado. identity.json local que use o mesmo device_id precisa da mesma
SignPrivateKey — senão POST /devices/{id}/frame retorna 401.
"""

from __future__ import annotations

# Guid do device seedado na API (TestDeviceSeed.Id)
DEVICE_ID = "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"

# Ed25519 raw private seed (hex) — TestDeviceSeed.SignPrivateKey
SIGN_PRIVATE_KEY = (
    "a1b2c3d4e5f60718293a4b5c6d7e8f90112233445566778899aabbccddeeff00"
)

# Ed25519 raw public key (hex) — TestDeviceSeed.SignPublicKey
SIGN_PUBLIC_KEY = (
    "42aaead72ceea9f9423f281440c6cfac7a5f99b796b81862f452328972b21b61"
)
