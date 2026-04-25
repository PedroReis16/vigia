from __future__ import annotations

from uuid import uuid4

import pytest

from app.fiware.models.vigia_settings import VigiaSettings
from app.fiware.requests.put_vigia_device import PutVigiaDevice


class _FakeResponse:
    def __init__(self, status: int, body: str = "") -> None:
        self.status = status
        self._body = body

    async def text(self) -> str:
        return self._body

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

    def put(self, *args, **kwargs) -> _FakeResponse:  # noqa: ANN002, ANN003
        return self._response


@pytest.mark.asyncio
async def test_execute_async_given_success_status_should_return_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.fiware.requests.put_vigia_device.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=204)),
    )

    request = PutVigiaDevice()
    settings = VigiaSettings(device_id=uuid4())

    await request.execute_async(settings)


@pytest.mark.asyncio
async def test_execute_async_given_error_status_should_raise_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.fiware.requests.put_vigia_device.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=500, body="internal error")),
    )

    request = PutVigiaDevice()
    settings = VigiaSettings(device_id=uuid4())

    with pytest.raises(Exception, match="Error updating device in FIWARE: 500 internal error"):
        await request.execute_async(settings)
