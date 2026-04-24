"""Integração: command_bus com HTTP real (upload de logs)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from app.integration.command_bus import build_dispatcher
from app.integration.models.vigia_settings import VigiaSettings
from app.integration.types import IntegrationContext

from .integration_settings_helpers import minimal_integration_settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dispatch_given_upload_logs_and_available_file_should_post_multipart_to_logs_api(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    log_file = tmp_path / "app.log"
    log_file.write_text("error line\n", encoding="utf-8")

    received: list[tuple[str, bytes]] = []

    async def ingest_logs(request: web.Request) -> web.StreamResponse:
        reader = await request.multipart()
        async for field in reader:
            if field.name == "logfile":
                received.append((field.filename or "", await field.read()))
        return web.Response(status=200)

    app = web.Application()
    app.router.add_post("/ingest", ingest_logs)

    async with TestServer(app) as logs_server:
        ingest_url = str(logs_server.make_url("/ingest"))
        monkeypatch.setenv("LOGS_API_URL", ingest_url)

        ctx = IntegrationContext(
            settings=minimal_integration_settings(),
            device_settings=VigiaSettings(device_id=uuid4()),
        )
        dispatcher = build_dispatcher(ctx)

        await dispatcher.dispatch("upload_logs", {"path": str(log_file)})

    assert received and received[0][0] == "app.log"
    assert b"error line" in received[0][1]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dispatch_given_upload_logs_without_logs_api_should_noop(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.delenv("LOGS_API_URL", raising=False)
    log_file = tmp_path / "missing.log"

    ctx = IntegrationContext(
        settings=minimal_integration_settings(),
        device_settings=VigiaSettings(device_id=uuid4()),
    )
    dispatcher = build_dispatcher(ctx)

    await dispatcher.dispatch("upload_logs", {"path": str(log_file)})


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dispatch_given_stream_command_should_invoke_default_handler(
    capsys: pytest.CaptureFixture[str],
) -> None:
    ctx = IntegrationContext(
        settings=minimal_integration_settings(),
        device_settings=VigiaSettings(device_id=uuid4()),
    )
    dispatcher = build_dispatcher(ctx)

    await dispatcher.dispatch("stream", {})

    captured = capsys.readouterr()
    assert "stream" in captured.out.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dispatch_given_unknown_command_should_not_raise(
    capsys: pytest.CaptureFixture[str],
) -> None:
    ctx = IntegrationContext(
        settings=minimal_integration_settings(),
        device_settings=VigiaSettings(device_id=uuid4()),
    )
    dispatcher = build_dispatcher(ctx)

    await dispatcher.dispatch("unknown_command_xyz", {})

    captured = capsys.readouterr()
    assert "nao suportado" in captured.out.lower()
