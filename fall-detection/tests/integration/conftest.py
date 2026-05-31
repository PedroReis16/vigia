"""Fixtures compartilhados para testes de integração HTTP (FIWARE simulado)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from aiohttp.test_utils import TestServer

from .fake_fiware_app import build_fake_fiware_app


@pytest.fixture
async def fiware_http_integration(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[tuple[TestServer, dict]]:
    """Sobe servidor local e define FIWARE_PATH para apontar para ele."""
    app, state = build_fake_fiware_app()
    async with TestServer(app) as server:
        root = str(server.make_url("/")).rstrip("/")
        monkeypatch.setenv("FIWARE_PATH", root)
        monkeypatch.setenv("FIWARE_SERVICE", "test-fiware-service")
        monkeypatch.delenv("ORION_COMMAND_PROVIDER_URL", raising=False)
        yield server, state
