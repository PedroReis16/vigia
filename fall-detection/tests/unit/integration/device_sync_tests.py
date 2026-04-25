from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.integration.device_registration import sync_device_registration
from app.fiware.models.vigia_settings import VigiaSettings


@pytest.mark.asyncio
async def test_sync_device_registration_given_non_exist_device_should_register_device() -> None:
    device_settings = VigiaSettings(device_id=uuid4())

    with (
        patch(
            "app.integration.device_registration.GetFiwareDeviceById.execute_async",
            new=AsyncMock(return_value=None),
        ) as get_mock,
        patch(
            "app.integration.device_registration.PostNewVigiaDevice.execute_async",
            new=AsyncMock(),
        ) as create_mock,
        patch(
            "app.integration.device_registration.PostVigiaCommand.execute_async",
            new=AsyncMock(),
        ) as command_mock,
        patch(
            "app.integration.device_registration.PutVigiaDevice.execute_async",
            new=AsyncMock(),
        ) as update_mock,
    ):
        await sync_device_registration(device_settings)

    get_mock.assert_awaited_once()
    create_mock.assert_awaited_once_with(device_settings)
    command_mock.assert_awaited_once_with(device_settings)
    update_mock.assert_not_called()


@pytest.mark.asyncio
async def test_sync_device_registration_given_device_with_diff_should_update_device() -> None:
    local_device = VigiaSettings(device_id=uuid4())
    remote_device = VigiaSettings(device_id=local_device.device_id, entity_type="OtherType")

    with (
        patch(
            "app.integration.device_registration.GetFiwareDeviceById.execute_async",
            new=AsyncMock(return_value=remote_device),
        ),
        patch(
            "app.integration.device_registration.PostNewVigiaDevice.execute_async",
            new=AsyncMock(),
        ) as create_mock,
        patch(
            "app.integration.device_registration.PostVigiaCommand.execute_async",
            new=AsyncMock(),
        ) as command_mock,
        patch(
            "app.integration.device_registration.PutVigiaDevice.execute_async",
            new=AsyncMock(),
        ) as update_mock,
    ):
        await sync_device_registration(local_device)

    create_mock.assert_not_called()
    command_mock.assert_not_called()
    update_mock.assert_awaited_once_with(local_device)
