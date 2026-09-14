#!/usr/bin/env python3
"""
Seed local do edge (bootstrap + fall) alinhado ao TestDeviceSeed da API (DEBUG).

Gera identity.json / network.json / classifier.json em ``edge-data/`` (default),
para rodar Vigia.Bootstrap e Vigia.Fall no Mac sem BLE, Pi, LCD ou Wi‑Fi real.

Pré-requisito: stack ``docker-compose/local`` com API em Debug (seed do device
no Postgres + FIWARE). Login admin: admin / admin123.

Uso:
  python seed-codes/seed_local_edge.py
  python seed-codes/seed_local_edge.py --api-base-url http://10.2.22.94:8090/vigia
  python seed-codes/seed_local_edge.py --data-dir /caminho/custom

Deps: pip install -r seed-codes/requirements.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

# Espelha Vigia.Models.Seed.TestDeviceSeed
DEVICE_ID = "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"
DEVICE_NAME = "Vigia-a1b2c3d4"
MAC_ADDRESS = "AA:BB:CC:DD:EE:FF"
_SIGN_PASSPHRASE = b"vigia-debug-test-device-v1"
_ECDH_PASSPHRASE = b"vigia-debug-test-device-ecdh-v1"
DEFAULT_API_BASE_URL = "http://localhost:8090/vigia"
DEFAULT_FIWARE_API_KEY = "VIGIA"
DEFAULT_STREAM_INGEST_URL = "rtmp://localhost:1935"
EXPECTED_SIGN_PUBLIC_KEY = (
    "10ef4349806050a8e17a82781f188165b70cd19d176c70ec5154c6d9ede4b59d"
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = REPO_ROOT / "edge-data"


def sign_private_key_hex() -> str:
    return hashlib.sha256(_SIGN_PASSPHRASE).hexdigest()


def ecdh_private_key_hex() -> str:
    return hashlib.sha256(_ECDH_PASSPHRASE).hexdigest()


def sign_public_key_hex(private_key_hex: str | None = None) -> str:
    seed = private_key_hex or sign_private_key_hex()
    priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))
    return priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()


def build_identity() -> dict[str, str]:
    sign_priv = sign_private_key_hex()
    pub = sign_public_key_hex(sign_priv)
    if pub != EXPECTED_SIGN_PUBLIC_KEY:
        raise RuntimeError(
            f"SignPublicKey derivada ({pub}) != TestDeviceSeed ({EXPECTED_SIGN_PUBLIC_KEY})"
        )
    # Valida que o seed ECDH é aceito pela lib (clamping interno na carga).
    X25519PrivateKey.from_private_bytes(bytes.fromhex(ecdh_private_key_hex()))
    return {
        "device_id": DEVICE_ID,
        "device_name": DEVICE_NAME,
        "mac_address": MAC_ADDRESS,
        "sign_priv": sign_priv,
        "ecdh_priv": ecdh_private_key_hex(),
    }


def build_network(
    api_base_url: str = DEFAULT_API_BASE_URL,
    fiware_api_key: str = DEFAULT_FIWARE_API_KEY,
    stream_ingest_url: str = DEFAULT_STREAM_INGEST_URL,
) -> dict[str, str]:
    return {
        "ssid": "local-mock",
        "password": "unused",
        "api_base_url": api_base_url.rstrip("/"),
        "fiware_api_key": fiware_api_key,
        "stream_ingest_url": stream_ingest_url.rstrip("/"),
    }


def build_classifier(classifier: str = "math") -> dict[str, str]:
    if classifier not in {"math", "gru"}:
        raise ValueError(f"classifier inválido: {classifier}")
    return {"classifier": classifier}


def write_json(path: Path, payload: dict, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, mode)


def seed_data_dir(
    data_dir: Path,
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    fiware_api_key: str = DEFAULT_FIWARE_API_KEY,
    stream_ingest_url: str = DEFAULT_STREAM_INGEST_URL,
    classifier: str = "math",
) -> dict[str, Path]:
    identity = build_identity()
    network = build_network(
        api_base_url=api_base_url,
        fiware_api_key=fiware_api_key,
        stream_ingest_url=stream_ingest_url,
    )
    classifier_doc = build_classifier(classifier)

    paths = {
        "identity": data_dir / "identity.json",
        "network": data_dir / "network.json",
        "classifier": data_dir / "classifier.json",
    }
    write_json(paths["identity"], identity, mode=0o600)
    write_json(paths["network"], network, mode=0o644)
    write_json(paths["classifier"], classifier_doc, mode=0o644)
    (data_dir / "ota").mkdir(parents=True, exist_ok=True)
    return paths


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera identity/network/classifier para bootstrap+fall local",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Diretório de saída (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--api-base-url",
        default=os.environ.get("VIGIA_API_BASE_URL", DEFAULT_API_BASE_URL),
        help="api_base_url gravado em network.json (frames + host MQTT)",
    )
    parser.add_argument(
        "--fiware-api-key",
        default=os.environ.get("VIGIA_FIWARE_API_KEY", DEFAULT_FIWARE_API_KEY),
        help="fiware_api_key (default: VIGIA)",
    )
    parser.add_argument(
        "--stream-ingest-url",
        default=os.environ.get(
            "VIGIA_STREAM_INGEST_URL", DEFAULT_STREAM_INGEST_URL
        ),
        help="URL base de publicação RTMP (default: rtmp://localhost:1935)",
    )
    parser.add_argument(
        "--classifier",
        choices=("math", "gru"),
        default="math",
        help="Preferência em classifier.json",
    )
    parser.add_argument(
        "--also-service-data",
        action="store_true",
        help="Também grava em vigia-bootstrap/data e vigia-fall/data",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    targets = [args.data_dir.resolve()]
    if args.also_service_data:
        targets.extend(
            [
                (REPO_ROOT / "vigia-bootstrap" / "data").resolve(),
                (REPO_ROOT / "vigia-fall" / "data").resolve(),
            ]
        )

    print(f"Device: {DEVICE_NAME} ({DEVICE_ID})")
    print(f"SignPublicKey: {sign_public_key_hex()}")
    print(f"api_base_url: {args.api_base_url}")

    for target in targets:
        paths = seed_data_dir(
            target,
            api_base_url=args.api_base_url,
            fiware_api_key=args.fiware_api_key,
            stream_ingest_url=args.stream_ingest_url,
            classifier=args.classifier,
        )
        print(f"Seeded {target}")
        for name, path in paths.items():
            print(f"  - {name}: {path}")

    print(
        "\nPróximos passos:\n"
        "  1. Stack local no ar (docker-compose/local) — API Debug seeda o device.\n"
        "  2. Confirme DATA_DIR=../edge-data nos .env de bootstrap e fall.\n"
        "  3. VS Code: compound Debug Edge (Bootstrap + Fall).\n"
        "  4. App: login admin/admin123 — device 'Câmera Teste' já no grupo Admin."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
