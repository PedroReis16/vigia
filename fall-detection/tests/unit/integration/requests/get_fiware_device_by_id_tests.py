from __future__ import annotations

from uuid import uuid4

import pytest

from app.integration.models.vigia_settings import VigiaSettings
from app.integration.requests.get_fiware_device_by_id import GetFiwareDeviceById


class _FakeResponse:
    def __init__(self, status: int, body: dict | None = None, text_body: str = "", content_type: str = "application/json") -> None:
        self.status = status
        self._body = body or {}
        self._text_body = text_body
        self.headers = {"Content-Type": content_type}

    async def json(self) -> dict:
        return self._body

    async def text(self) -> str:
        return self._text_body

    async def __aenter__(self) -> _FakeResponse:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeClientSession:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    async def __aenter__(self) -> _FakeClientSession:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, *args, **kwargs) -> _FakeResponse:  # noqa: ANN002, ANN003
        return self._response


@pytest.mark.asyncio
async def test_execute_async_given_not_found_status_should_return_none(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integration.requests.get_fiware_device_by_id.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=404)),
    )

    result = await GetFiwareDeviceById().execute_async(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_execute_async_given_non_json_response_should_return_none(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integration.requests.get_fiware_device_by_id.aiohttp.ClientSession",
        lambda: _FakeClientSession(
            _FakeResponse(status=200, content_type="text/html", text_body="<html/>")
        ),
    )

    result = await GetFiwareDeviceById().execute_async(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_execute_async_given_ok_json_response_should_return_vigia_settings(monkeypatch) -> None:
    device_id = uuid4()
    monkeypatch.setattr(
        "app.integration.requests.get_fiware_device_by_id.aiohttp.ClientSession",
        lambda: _FakeClientSession(
            _FakeResponse(
                status=200,
                body={"device": {"device_id": str(device_id)}},
            )
        ),
    )

    result = await GetFiwareDeviceById().execute_async(device_id)

    assert isinstance(result, VigiaSettings)
    assert result.device_id == device_id


@pytest.mark.asyncio
async def test_execute_async_given_non_success_status_should_raise_exception(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integration.requests.get_fiware_device_by_id.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=500, text_body="boom")),
    )

    with pytest.raises(Exception, match="Error fetching FIWARE device: 500 boom"):
        await GetFiwareDeviceById().execute_async(uuid4())
