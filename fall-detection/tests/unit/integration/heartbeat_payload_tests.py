from app.integration.models.heartbeat_payload import HeartbeatPayload


def test_to_attrs_payload_given_valid_payload_should_return_expected_shape() -> None:
    payload = HeartbeatPayload(
        entity_id="urn:ngsi-ld:VigiaCam:1234",
        entity_type="VigiaCam",
        heartbeat_at="2026-04-21T20:00:00Z",
        device_ip="192.168.0.100",
        capture_status="running",
        core_status="running",
    )

    assert payload.to_attrs_payload() == {
        "heartbeatAt": {"type": "DateTime", "value": "2026-04-21T20:00:00Z"},
        "deviceIp": {"type": "Text", "value": "192.168.0.100"},
        "captureStatus": {"type": "Text", "value": "running"},
        "coreStatus": {"type": "Text", "value": "running"},
    }


def test_to_create_payload_given_valid_payload_should_include_identity_fields() -> None:
    payload = HeartbeatPayload(
        entity_id="urn:ngsi-ld:VigiaCam:1234",
        entity_type="VigiaCam",
        heartbeat_at="2026-04-21T20:00:00Z",
        device_ip="192.168.0.100",
        capture_status="running",
        core_status="running",
    )

    create_payload = payload.to_create_payload()

    assert create_payload["id"] == "urn:ngsi-ld:VigiaCam:1234"
    assert create_payload["type"] == "VigiaCam"
    assert "heartbeatAt" in create_payload


def test_expected_schema_given_default_contract_should_return_supported_schema() -> None:
    assert HeartbeatPayload.expected_schema() == {
        "heartbeatAt": "DateTime",
        "deviceIp": "Text",
        "captureStatus": "Text",
        "coreStatus": "Text",
    }
