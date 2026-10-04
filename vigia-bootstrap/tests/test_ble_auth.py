from provision.ble import _legacy_stream_ingest_url


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
