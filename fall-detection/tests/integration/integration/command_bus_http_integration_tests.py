"""Integração: command_bus com HTTP real (upload de logs)."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import app.integration.command_bus as command_bus_module
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from app.fiware.models.vigia_settings import VigiaSettings
from app.integration.command_bus import build_dispatcher
from app.integration.types import IntegrationContext

from .integration_settings_helpers import minimal_integration_settings


@pytest.fixture(autouse=True)
def reset_streaming_process_state() -> None:
    command_bus_module._streaming_process = None
    yield
    command_bus_module._streaming_process = None


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
async def test_dispatch_given_stream_command_without_ingest_url_should_warn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged: list[str] = []

    def fake_warning(message: str, *_args: object) -> None:
        logged.append(message)

    monkeypatch.setattr("app.integration.command_bus.logger.warning", fake_warning)

    ctx = IntegrationContext(
        settings=minimal_integration_settings(stream_ingest_url=""),
        device_settings=VigiaSettings(device_id=uuid4()),
    )
    dispatcher = build_dispatcher(ctx)

    await dispatcher.dispatch("stream", {})

    assert any("STREAM_INGEST" in message or "nao configurada" in message for message in logged)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dispatch_given_stream_command_with_ingest_should_start_dummy_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged: list[str] = []

    def fake_info(message: str, *args: object) -> None:
        logged.append(message)

    monkeypatch.setattr("app.integration.command_bus.logger.info", fake_info)

    class DummyProcess:
        def __init__(self, *_a: object, **_k: object) -> None:
            self._alive = False
            self.pid = 99999

        def start(self) -> None:
            self._alive = True

        def is_alive(self) -> bool:
            return self._alive

        def terminate(self) -> None:
            self._alive = False

        def join(self, timeout: float | None = None) -> None:
            return None

    monkeypatch.setattr(
        command_bus_module,
        "_spawn_ctx",
        SimpleNamespace(Process=DummyProcess),
    )

    ctx = IntegrationContext(
        settings=minimal_integration_settings(stream_ingest_url="rtmp://localhost/live"),
        device_settings=VigiaSettings(device_id=uuid4()),
    )
    dispatcher = build_dispatcher(ctx)

    await dispatcher.dispatch("stream", {})

    assert any("streaming iniciado" in message.lower() for message in logged)

    await dispatcher.dispatch("stream", {"value": "off"})
    assert any("encerrado" in message.lower() or "parado" in message.lower() for message in logged)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dispatch_given_unknown_command_should_not_raise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged_messages: list[str] = []

    def fake_warning(message: str, *_args: object) -> None:
        logged_messages.append(message)

    monkeypatch.setattr("app.integration.command_bus.logger.warning", fake_warning)

    ctx = IntegrationContext(
        settings=minimal_integration_settings(),
        device_settings=VigiaSettings(device_id=uuid4()),
    )
    dispatcher = build_dispatcher(ctx)

    await dispatcher.dispatch("unknown_command_xyz", {})

    assert any("nao suportado" in message.lower() for message in logged_messages)
