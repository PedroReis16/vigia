from __future__ import annotations

import pytest

from app.fiware.requests.get_orion_entity_by_id import GetOrionEntityById


class _FakeResponse:
    def __init__(self, status: int, body: dict | None = None, text_body: str = "") -> None:
        self.status = status
        self._body = body or {}
        self._text_body = text_body

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
        "app.fiware.requests.get_orion_entity_by_id.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=404)),
    )
    result = await GetOrionEntityById().execute_async("urn:test:1")
    assert result is None


@pytest.mark.asyncio
async def test_execute_async_given_ok_status_should_return_entity(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.fiware.requests.get_orion_entity_by_id.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=200, body={"id": "urn:test:1"})),
    )
    result = await GetOrionEntityById().execute_async("urn:test:1")
    assert result == {"id": "urn:test:1"}


@pytest.mark.asyncio
async def test_execute_async_given_non_success_status_should_raise_exception(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.fiware.requests.get_orion_entity_by_id.aiohttp.ClientSession",
        lambda: _FakeClientSession(_FakeResponse(status=500, text_body="boom")),
    )

    with pytest.raises(Exception, match="Error fetching Orion entity: 500 boom"):
        await GetOrionEntityById().execute_async("urn:test:1")
