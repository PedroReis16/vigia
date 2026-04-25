import os

from app.fiware.requests.fiware_endpoints import (
    fiware_root_url,
    iot_agent_url,
    orion_url,
    sth_comet_url,
)


def test_fiware_root_url_given_trailing_slash_should_trim_suffix(monkeypatch) -> None:
    monkeypatch.setenv("FIWARE_PATH", "https://www.vigia-deteccoes.duckdns.org/")
    assert fiware_root_url() == "https://www.vigia-deteccoes.duckdns.org"


def test_iot_agent_url_given_fiware_path_should_append_iot_agent_prefix(monkeypatch) -> None:
    monkeypatch.setenv("FIWARE_PATH", "https://www.vigia-deteccoes.duckdns.org")
    assert iot_agent_url() == "https://www.vigia-deteccoes.duckdns.org/iot-agent"


def test_orion_url_given_fiware_path_should_append_orion_prefix(monkeypatch) -> None:
    monkeypatch.setenv("FIWARE_PATH", "https://www.vigia-deteccoes.duckdns.org")
    assert orion_url() == "https://www.vigia-deteccoes.duckdns.org/orion"


def test_sth_comet_url_given_fiware_path_should_append_sth_comet_prefix(monkeypatch) -> None:
    monkeypatch.setenv("FIWARE_PATH", "https://www.vigia-deteccoes.duckdns.org")
    assert sth_comet_url() == "https://www.vigia-deteccoes.duckdns.org/sth-comet"
