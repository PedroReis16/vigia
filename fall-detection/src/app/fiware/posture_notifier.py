from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.fiware.device_sync import load_local_device_settings_required
from app.fiware.models.heartbeat_payload import HeartbeatPayload
from app.fiware.posture_state import write_posture_state
from app.fiware.requests.post_create_device_heartbeat_entity import (
    CreateDeviceHeartbeatEntityError,
    PostCreateDeviceHeartbeatEntity,
)
from app.fiware.requests.post_update_device_heartbeat_attrs import (
    PostUpdateDeviceHeartbeatAttrs,
    UpdateDeviceHeartbeatAttrsError,
)
from app.logging import get_logger

logger = get_logger("fiware")


class FiwarePostureNotifier:
    """Publica mudanças de postura no Orion usando os clientes FIWARE padrão."""

    def __init__(self) -> None:
        self._device_settings = load_local_device_settings_required()
        self._create_request = PostCreateDeviceHeartbeatEntity()
        self._update_request = PostUpdateDeviceHeartbeatAttrs()

    def notify_posture_changed(self, posture_state: str) -> None:
        changed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        write_posture_state(posture_state, changed_at)
        asyncio.run(self._notify_orion(posture_state, changed_at))

    async def _notify_orion(self, posture_state: str, changed_at: str) -> None:
        attrs_payload = {
            "postureState": {"type": "Text", "value": posture_state},
            "postureChangedAt": {"type": "DateTime", "value": changed_at},
        }
        entity_id = self._device_settings.entity_name

        try:
            await self._update_request.execute_async(entity_id, attrs_payload)
            logger.debug("postura atualizada no FIWARE: {}", posture_state)
            return
        except UpdateDeviceHeartbeatAttrsError as exc:
            if exc.status_code != 404:
                logger.warning("falha ao atualizar postura no FIWARE: {}", exc)
                return

        try:
            payload = HeartbeatPayload(
                entity_id=entity_id,
                entity_type=self._device_settings.entity_type,
                heartbeat_at=changed_at,
                device_ip="unknown",
                capture_status="running",
                core_status="unknown",
                posture_state=posture_state,
                posture_changed_at=changed_at,
            )
            await self._create_request.execute_async(payload.to_create_payload())
            logger.info("entidade heartbeat criada no FIWARE para enviar postura")
        except CreateDeviceHeartbeatEntityError as create_exc:
            if (
                create_exc.status_code == 422
                and "Already Exists" in create_exc.response_text
            ):
                try:
                    await self._update_request.execute_async(entity_id, attrs_payload)
                    logger.debug("postura atualizada no FIWARE: {}", posture_state)
                except UpdateDeviceHeartbeatAttrsError as update_exc:
                    logger.warning(
                        "falha ao atualizar postura no FIWARE após 422: {}", update_exc
                    )
            else:
                logger.warning("falha ao criar entidade heartbeat: {}", create_exc)
