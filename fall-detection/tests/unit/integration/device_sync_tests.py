from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.integration.device_sync import ensure_fiware_device_synced
from app.integration.models.vigia_settings import VigiaSettings


@pytest.mark.asyncio
async def test_ensure_fiware_device_synced_given_non_exist_device_should_register_device() -> None:
    device_settings = VigiaSettings(device_id=uuid4())

    with (
        patch(
            "app.integration.device_sync.GetFiwareDeviceById.execute_async",
            new=AsyncMock(return_value=None),
        ) as get_mock,
        patch(
            "app.integration.device_sync.PostNewVigiaDevice.execute_async",
            new=AsyncMock(),
        ) as create_mock,
        patch(
            "app.integration.device_sync.PostVigiaCommand.execute_async",
            new=AsyncMock(),
        ) as command_mock,
        patch(
            "app.integration.device_sync.PutVigiaDevice.execute_async",
            new=AsyncMock(),
        ) as update_mock,
    ):
        await ensure_fiware_device_synced(device_settings)

    get_mock.assert_awaited_once()
    create_mock.assert_awaited_once_with(device_settings)
    command_mock.assert_awaited_once_with(device_settings)
    update_mock.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_fiware_device_synced_given_device_with_diff_should_update_device() -> None:
    local_device = VigiaSettings(device_id=uuid4())
    remote_device = VigiaSettings(device_id=local_device.device_id, entity_type="OtherType")

    with (
        patch(
            "app.integration.device_sync.GetFiwareDeviceById.execute_async",
            new=AsyncMock(return_value=remote_device),
        ),
        patch(
            "app.integration.device_sync.PostNewVigiaDevice.execute_async",
            new=AsyncMock(),
        ) as create_mock,
        patch(
            "app.integration.device_sync.PostVigiaCommand.execute_async",
            new=AsyncMock(),
        ) as command_mock,
        patch(
            "app.integration.device_sync.PutVigiaDevice.execute_async",
            new=AsyncMock(),
        ) as update_mock,
    ):
        await ensure_fiware_device_synced(local_device)

    create_mock.assert_not_called()
    command_mock.assert_not_called()
    update_mock.assert_awaited_once_with(local_device)
