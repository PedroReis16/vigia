from __future__ import annotations

from worker.mqtt import mqtt_endpoint, parse_ultralight_command


def test_parse_ultralight_command():
    assert parse_ultralight_command("dev@stream_on|") == ("dev", "stream_on", "")
    assert parse_ultralight_command("dev@device_update|rev1") == (
        "dev",
        "device_update",
        "rev1",
    )
    assert parse_ultralight_command("invalid") is None


def test_mqtt_endpoint_local_maps_8090_to_81():
    host, port, path, use_tls = mqtt_endpoint("http://localhost:8090/vigia")
    assert host == "localhost"
    assert port == 81
    assert path == "/vigia/fiware/mosquitto"
    assert use_tls is False


def test_mqtt_endpoint_local_keeps_traefik_81():
    host, port, path, use_tls = mqtt_endpoint("http://localhost:81/vigia")
    assert host == "localhost"
    assert port == 81
    assert path == "/vigia/fiware/mosquitto"
    assert use_tls is False
