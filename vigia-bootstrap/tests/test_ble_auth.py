import base64

import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from provision.ble import _decode_ed25519_field, _parse_auth_payload


def test_decode_ed25519_field_hex_and_base64() -> None:
    material = b"\x01" * 32
    assert _decode_ed25519_field(material.hex(), 32) == material
    assert _decode_ed25519_field(base64.b64encode(material).decode(), 32) == material


def test_parse_auth_payload_accepts_base64() -> None:
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes_raw()
    nonce = b"\xab" * 16
    sig_bytes = private_key.sign(nonce)

    payload = {
        "app_sign_pub": base64.b64encode(pub_bytes).decode(),
        "signature": base64.b64encode(sig_bytes).decode(),
    }

    parsed_pub, parsed_sig = _parse_auth_payload(payload)
    assert parsed_pub == pub_bytes
    public_key.verify(parsed_sig, nonce)


def test_parse_auth_payload_accepts_hex_legacy() -> None:
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes_raw()
    nonce = b"\xcd" * 16
    sig_bytes = private_key.sign(nonce)

    payload = {
        "app_sign_pub": pub_bytes.hex(),
        "signature": sig_bytes.hex(),
    }

    parsed_pub, parsed_sig = _parse_auth_payload(payload)
    assert parsed_pub == pub_bytes
    public_key.verify(parsed_sig, nonce)
