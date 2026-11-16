import json

from interface.provision import state
from interface.provision.ble import (
    CHAR_IDENTITY_UUID,
    CHAR_PROVISION_UUID,
    _legacy_stream_ingest_url,
    __read_request,
    __write_request,
    device_context,
)


class _Char:
    def __init__(self, uuid: str) -> None:
        self.uuid = uuid
        self.value = bytearray()


def test_legacy_stream_ingest_url_production() -> None:
    assert (
        _legacy_stream_ingest_url("https://services.vigiadeteccoes.com.br/vigia")
        == "rtmps://ingest.vigiadeteccoes.com.br:8443"
    )


def test_legacy_stream_ingest_url_local() -> None:
    assert (
        _legacy_stream_ingest_url("http://host.docker.internal:81/vigia")
        == "rtmp://host.docker.internal:1935"
    )


def test_read_identity_sem_chaves() -> None:
    device_context.clear()
    device_context.update(
        {
            "device_id": "11111111-1111-1111-1111-111111111111",
            "device_name": "Vigia-test",
            "mac_address": "aa:bb:cc:dd:ee:ff",
        }
    )
    characteristic = _Char(CHAR_IDENTITY_UUID)

    raw = __read_request(characteristic)

    packet = json.loads(bytes(raw).decode())
    assert packet == {
        "device_id": "11111111-1111-1111-1111-111111111111",
        "name": "Vigia-test",
        "mac_address": "aa:bb:cc:dd:ee:ff",
    }
    assert "sign_pub" not in packet
    assert "ecdh_pub" not in packet
    device_context.clear()
    state.set_pairing_stage(state.WAITING_APP)


def test_provision_write_sem_sessao_autenticada(monkeypatch) -> None:
    device_context.clear()
    scheduled: list[object] = []

    class _Loop:
        def create_task(self, coro):
            scheduled.append(coro)
            coro.close()

    monkeypatch.setattr("interface.provision.ble.loop", _Loop())
    characteristic = _Char(CHAR_PROVISION_UUID)
    payload = json.dumps(
        {
            "ssid": "casa",
            "pass": "segredo",
            "api": "http://api.test/vigia",
            "fiware": "k",
            "stream_ingest_url": "rtmp://ingest.test:1935",
        }
    ).encode()

    __write_request(characteristic, payload)

    assert bytes(characteristic.value) == b"CONNECTING"
    assert scheduled
    assert "authenticated_session" not in device_context
    device_context.clear()
    state.set_pairing_stage(state.WAITING_APP)
