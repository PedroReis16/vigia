from __future__ import annotations

import pytest

from app.integration.requests.post_update_device_heartbeat_attrs import (
    PostUpdateDeviceHeartbeatAttrs,
    UpdateDeviceHeartbeatAttrsError,
)


class _FakeResponse:
    def __init__(self, status: int, text_body: str = "") -> None:
        self.status = status
        self._text_body = text_body

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

    def post(self, *args, **kwargs) -> _FakeResponse:  # noqa: ANN002, ANN003
        return self._response


@pytest.mark.asyncio
async def test_execute_async_given_success_status_should_return_none(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integration.requests.post_update_device_heartbeat_attrs.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=204)),
    )

    await PostUpdateDeviceHeartbeatAttrs().execute_async("urn:test:heartbeat", {"a": 1})


@pytest.mark.asyncio
async def test_execute_async_given_error_status_should_raise_update_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integration.requests.post_update_device_heartbeat_attrs.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=500, text_body="boom")),
    )

    with pytest.raises(UpdateDeviceHeartbeatAttrsError):
        await PostUpdateDeviceHeartbeatAttrs().execute_async("urn:test:heartbeat", {"a": 1})
