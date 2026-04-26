from __future__ import annotations

import asyncio
import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.config import Settings
from app.fiware.models.heartbeat_payload import HeartbeatPayload
from app.fiware.models.vigia_settings import VigiaSettings
from app.fiware.posture_state import read_posture_state
from app.fiware.requests.get_orion_entity_by_id import GetOrionEntityById
from app.fiware.requests.post_create_device_heartbeat_entity import (
    CreateDeviceHeartbeatEntityError,
    PostCreateDeviceHeartbeatEntity,
)
from app.fiware.requests.post_update_device_heartbeat_attrs import (
    PostUpdateDeviceHeartbeatAttrs,
    UpdateDeviceHeartbeatAttrsError,
)
from app.logging import get_logger

ModuleStatusProvider = Callable[[], str]
_MODULE_STATUS_PROVIDERS: dict[str, ModuleStatusProvider] = {}
logger = get_logger("integration")


def register_module_status_provider(
    module_name: str, provider: ModuleStatusProvider
) -> None:
    """Permite aos módulos reportarem o próprio status no heartbeat."""
    _MODULE_STATUS_PROVIDERS[module_name.lower()] = provider


def _resolve_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return str(sock.getsockname()[0])
    except OSError:
        return "unknown"


def _module_status(module_name: str) -> str:
    file_status = _module_status_from_file(module_name)
    if file_status is not None:
        return file_status

    provider = _MODULE_STATUS_PROVIDERS.get(module_name.lower())
    if provider is None:
        return "unknown"
    try:
        return str(provider())
    except Exception as exc:  # pragma: no cover
        logger.warning("erro lendo status do modulo {}: {}", module_name, exc)
        return "error"


def _module_status_from_file(module_name: str) -> str | None:
    status_file_raw = (os.getenv("MODULE_STATUS_FILE") or "").strip()
    if not status_file_raw:
        return None

    status_file = Path(status_file_raw)
    if not status_file.exists():
        return None

    try:
        content = status_file.read_text(encoding="utf-8").strip()
        if not content:
            return None
        payload = json.loads(content)
        value = payload.get(module_name.lower())
        if value is None:
            return None
        return str(value)
    except Exception as exc:  # pragma: no cover
        logger.warning("erro lendo MODULE_STATUS_FILE: {}", exc)
        return None


def _build_heartbeat_payload(device_settings: VigiaSettings) -> HeartbeatPayload:
    heartbeat_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    posture_state, posture_changed_at = read_posture_state()
    return HeartbeatPayload(
        entity_id=device_settings.entity_name,
        entity_type=device_settings.entity_type,
        heartbeat_at=heartbeat_at,
        device_ip=_resolve_local_ip(),
        capture_status=_module_status("capture"),
        core_status=_module_status("core"),
        posture_state=posture_state,
        posture_changed_at=posture_changed_at or heartbeat_at,
    )


def _is_schema_outdated(remote_entity: dict, expected_schema: dict[str, str]) -> bool:
    for attr_name, expected_type in expected_schema.items():
        remote_attr = remote_entity.get(attr_name)
        if not isinstance(remote_attr, dict):
            return True
        if str(remote_attr.get("type") or "") != expected_type:
            return True
    return False


async def _sync_heartbeat_schema(
    device_settings: VigiaSettings,
    create_requester: PostCreateDeviceHeartbeatEntity,
    update_requester: PostUpdateDeviceHeartbeatAttrs,
) -> bool:
    get_requester = GetOrionEntityById()
    payload = _build_heartbeat_payload(device_settings)
    remote_entity = await get_requester.execute_async(device_settings.entity_name)

    if remote_entity is None:
        await create_requester.execute_async(payload.to_create_payload())
        logger.info("entidade de heartbeat criada no FIWARE")
        return True

    if _is_schema_outdated(remote_entity, HeartbeatPayload.expected_schema()):
        await update_requester.execute_async(
            device_settings.entity_name, payload.to_attrs_payload()
        )
        logger.info("schema do heartbeat atualizado no FIWARE")
    return True


async def run_heartbeat_loop(settings: Settings, device_settings: VigiaSettings) -> None:
    interval_seconds = int(
        os.getenv("HEARTBEAT_INTERVAL_SECONDS", str(settings.integration_interval_seconds))
    )
    if interval_seconds <= 0:
        interval_seconds = settings.integration_interval_seconds

    create_requester = PostCreateDeviceHeartbeatEntity()
    update_requester = PostUpdateDeviceHeartbeatAttrs()
    entity_created = False

    try:
        entity_created = await _sync_heartbeat_schema(
            device_settings, create_requester, update_requester
        )
    except Exception as exc:
        logger.warning("falha ao sincronizar schema heartbeat: {}", exc)

    while True:
        payload = _build_heartbeat_payload(device_settings)
        attrs_payload = payload.to_attrs_payload()
        try:
            if not entity_created:
                await create_requester.execute_async(payload.to_create_payload())
                entity_created = True
                logger.info("entidade de heartbeat criada no FIWARE")
            else:
                await update_requester.execute_async(
                    device_settings.entity_name,
                    attrs_payload,
                )
            logger.debug("heartbeat enviado para o FIWARE")
        except CreateDeviceHeartbeatEntityError as exc:
            if exc.status_code == 422 and "Already Exists" in exc.response_text:
                entity_created = True
                try:
                    await update_requester.execute_async(
                        device_settings.entity_name,
                        attrs_payload,
                    )
                    logger.debug("heartbeat enviado para o FIWARE")
                except UpdateDeviceHeartbeatAttrsError as update_exc:
                    logger.warning("falha ao enviar heartbeat: {}", update_exc)
            else:
                logger.warning("falha ao enviar heartbeat: {}", exc)
        except UpdateDeviceHeartbeatAttrsError as exc:
            if exc.status_code == 404:
                entity_created = False
                logger.warning(
                    "entidade heartbeat nao encontrada; nova tentativa de criacao no proximo ciclo."
                )
            else:
                logger.warning("falha ao enviar heartbeat: {}", exc)
        except Exception as exc:
            logger.warning("falha ao enviar heartbeat: {}", exc)
        await asyncio.sleep(interval_seconds)
