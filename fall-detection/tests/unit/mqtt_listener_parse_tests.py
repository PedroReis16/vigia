"""Parsing de payloads MQTT: NGSI/JSON e Ultralight do IoT Agent."""

from __future__ import annotations

import json

from app.integration.mqtt_listener import _parse_command_payload


def test_parse_command_payload_given_ultralight_stream_should_extract_command() -> None:
    raw = "5be5d41e-5ac6-4a6c-b54f-becaf3b58594@stream|"
    name, payload = _parse_command_payload(raw)
    assert name == "stream"
    assert payload.get("value") == ""


def test_parse_command_payload_given_ultralight_with_value_should_extract() -> None:
    raw = "dev@ping|22"
    name, payload = _parse_command_payload(raw)
    assert name == "ping"
    assert payload.get("value") == "22"


def test_parse_command_payload_given_json_command_should_work() -> None:
    raw = json.dumps({"command": "stream", "payload": {"x": 1}})
    name, payload = _parse_command_payload(raw)
    assert name == "stream"
    assert isinstance(payload, dict)


def test_parse_command_payload_given_invalid_body_should_return_none() -> None:
    assert _parse_command_payload("garbage no at signs") is None
