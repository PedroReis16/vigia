"""Testes do seed local do edge (sem I/O de rede)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SEED_CODES = Path(__file__).resolve().parent
if str(SEED_CODES) not in sys.path:
    sys.path.insert(0, str(SEED_CODES))

import seed_local_edge as seed  # noqa: E402


class SeedLocalEdgeTests(unittest.TestCase):
    def test_sign_public_key_matches_test_device_seed(self) -> None:
        self.assertEqual(seed.sign_public_key_hex(), seed.EXPECTED_SIGN_PUBLIC_KEY)

    def test_identity_fields(self) -> None:
        identity = seed.build_identity()
        self.assertEqual(identity["device_id"], seed.DEVICE_ID)
        self.assertEqual(identity["device_name"], seed.DEVICE_NAME)
        self.assertEqual(identity["mac_address"], seed.MAC_ADDRESS)
        self.assertEqual(len(identity["sign_priv"]), 64)
        self.assertEqual(len(identity["ecdh_priv"]), 64)

    def test_network_strips_trailing_slash(self) -> None:
        network = seed.build_network(api_base_url="http://localhost:8090/vigia/")
        self.assertEqual(network["api_base_url"], "http://localhost:8090/vigia")
        self.assertEqual(network["fiware_api_key"], "VIGIA")

    def test_seed_data_dir_writes_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = seed.seed_data_dir(root)
            identity = json.loads(paths["identity"].read_text())
            network = json.loads(paths["network"].read_text())
            classifier = json.loads(paths["classifier"].read_text())
            self.assertEqual(identity["device_name"], "Vigia-a1b2c3d4")
            self.assertEqual(network["ssid"], "local-mock")
            self.assertEqual(classifier["classifier"], "math")
            self.assertTrue((root / "ota").is_dir())


if __name__ == "__main__":
    unittest.main()
