from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.integration.heartbeat import _sync_heartbeat_schema
from app.integration.models.vigia_settings import VigiaSettings


@pytest.mark.asyncio
async def test_sync_heartbeat_schema_given_non_exist_entity_should_create_entity() -> None:
    settings = VigiaSettings(device_id=uuid4())
    create_requester = AsyncMock()
    update_requester = AsyncMock()

    with patch(
        "app.integration.heartbeat.GetOrionEntityById.execute_async",
        new=AsyncMock(return_value=None),
    ):
        result = await _sync_heartbeat_schema(
            settings,
            create_requester=create_requester,
            update_requester=update_requester,
        )

    assert result is True
    create_requester.execute_async.assert_awaited_once()
    update_requester.execute_async.assert_not_called()


@pytest.mark.asyncio
async def test_sync_heartbeat_schema_given_outdated_schema_should_update_entity() -> None:
    settings = VigiaSettings(device_id=uuid4())
    create_requester = AsyncMock()
    update_requester = AsyncMock()
    remote_entity = {
        "id": settings.entity_name,
        "type": settings.entity_type,
        "heartbeatAt": {"type": "Text", "value": "wrong-type"},
        "deviceIp": {"type": "Text", "value": "10.0.0.5"},
        "captureStatus": {"type": "Text", "value": "running"},
        "coreStatus": {"type": "Text", "value": "running"},
    }

    with patch(
        "app.integration.heartbeat.GetOrionEntityById.execute_async",
        new=AsyncMock(return_value=remote_entity),
    ):
        result = await _sync_heartbeat_schema(
            settings,
            create_requester=create_requester,
            update_requester=update_requester,
        )

    assert result is True
    create_requester.execute_async.assert_not_called()
    update_requester.execute_async.assert_awaited_once()
