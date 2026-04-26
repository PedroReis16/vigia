from __future__ import annotations

from uuid import uuid4

import pytest

from app.fiware.models.vigia_settings import VigiaSettings
from app.fiware.requests.post_vigia_command import PostVigiaCommand


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
        "app.fiware.requests.post_vigia_command.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=204)),
    )

    await PostVigiaCommand().execute_async(VigiaSettings(device_id=uuid4()))


@pytest.mark.asyncio
async def test_execute_async_given_error_status_should_raise_exception(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.fiware.requests.post_vigia_command.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=500, text_body="invalid payload")),
    )

    with pytest.raises(Exception, match="Error posting command to FIWARE: 500 invalid payload"):
        await PostVigiaCommand().execute_async(VigiaSettings(device_id=uuid4()))
