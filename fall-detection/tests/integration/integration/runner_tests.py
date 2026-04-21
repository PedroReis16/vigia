from unittest.mock import AsyncMock, patch

import pytest

from app.config import Settings
from app.integration.runner import run_integration


@pytest.mark.asyncio
async def test_run_integration_given_valid_settings_should_wire_components() -> None:
    settings = Settings(
        data_path="data",
        frames_dir="data/frames",
        stream_video=False,
        stream_ingest_url="",
        stream_ingest_token="",
        stream_target=None,
        captures_per_second=10,
        video_capture_source=0,
        show_video=False,
        yolo_model="yolo26s",
        yolo_pose_model="yolo26s-pose",
        yolo_model_device="cpu",
        pose_csv_window_seconds=3,
        integration_interval_seconds=3,
    )
    fake_device_settings = object()

    with (
        patch(
            "app.integration.runner.load_or_create_local_device_settings",
            return_value=fake_device_settings,
        ) as load_mock,
        patch(
            "app.integration.runner.ensure_fiware_device_synced",
            new=AsyncMock(),
        ) as sync_mock,
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

    load_mock.assert_called_once()
    sync_mock.assert_awaited_once_with(fake_device_settings)
    dispatcher_mock.assert_called_once()
    heartbeat_mock.assert_awaited_once()
    mqtt_mock.assert_awaited_once_with(fake_device_settings, "dispatcher")
