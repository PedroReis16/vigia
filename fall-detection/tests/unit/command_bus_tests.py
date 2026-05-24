from unittest.mock import AsyncMock

import pytest

from app.integration.command_bus import CommandDispatcher, register_command_handler
from app.integration.types import IntegrationContext


@pytest.mark.asyncio
async def test_dispatch_given_registered_handler_should_call_handler() -> None:
    context = IntegrationContext(settings=object(), device_settings=object())
    dispatcher = CommandDispatcher(context)
    handler = AsyncMock()
    dispatcher.register("stream", handler)

    await dispatcher.dispatch("stream", {"enabled": True})

    handler.assert_awaited_once_with({"enabled": True})


@pytest.mark.asyncio
async def test_dispatch_given_unknown_command_should_not_raise_error() -> None:
    context = IntegrationContext(settings=object(), device_settings=object())
    dispatcher = CommandDispatcher(context)

    await dispatcher.dispatch("unknown", {"foo": "bar"})


def test_register_command_handler_given_new_handler_should_store_case_insensitive_key() -> None:
    async def _handler(_payload: dict) -> None:
        return None

    register_command_handler("ReStArT_Core", _handler)
