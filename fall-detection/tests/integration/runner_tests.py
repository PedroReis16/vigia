from unittest.mock import AsyncMock, patch

import pytest

from app.config import Settings
from app.integration.runner import run_integration


@pytest.mark.asyncio
async def test_run_integration_given_valid_settings_should_wire_components() -> None:
    settings = Settings(
        data_path="data",
        stream_ingest_url="",
        captures_per_second=10,
        video_capture_source=0,
        show_video=False,
        yolo_pose_model="yolo26s-pose",
        pose_csv_window_seconds=3,
        integration_interval_seconds=3,
    )
    fake_device_settings = object()

    with (
        patch(
            "app.integration.runner.bootstrap_device_registration",
            return_value=fake_device_settings,
            new_callable=AsyncMock,
        ) as bootstrap_mock,
        patch(
            "app.integration.runner.build_dispatcher",
            return_value="dispatcher",
        ) as dispatcher_mock,
        patch(
            "app.integration.runner.run_heartbeat_loop",
            new=AsyncMock(),
        ) as heartbeat_mock,
        patch(
            "app.integration.runner.listen_mqtt_commands",
            new=AsyncMock(),
        ) as mqtt_mock,
    ):
        await run_integration(settings)

    bootstrap_mock.assert_awaited_once()
    dispatcher_mock.assert_called_once()
    heartbeat_mock.assert_awaited_once()
    mqtt_mock.assert_awaited_once_with(fake_device_settings, "dispatcher")
