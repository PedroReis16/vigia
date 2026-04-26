"""
Módulo para o fluxo de integração da aplicação com o FIWARE
"""

from app.fiware.requests.get_fiware_device_by_id import GetFiwareDeviceById
from app.fiware.requests.get_orion_entity_by_id import GetOrionEntityById
from app.fiware.requests.post_create_device_heartbeat_entity import (
    PostCreateDeviceHeartbeatEntity,
)
from app.fiware.requests.post_device_heartbeat import PostDeviceHeartbeat
from app.fiware.requests.post_new_vigia_device import PostNewVigiaDevice
from app.fiware.requests.post_update_device_heartbeat_attrs import (
    PostUpdateDeviceHeartbeatAttrs,
)
from app.fiware.requests.post_vigia_command import PostVigiaCommand
from app.fiware.requests.put_vigia_device import PutVigiaDevice

from .command_bus import register_command_handler
from .heartbeat import register_module_status_provider
from .runner import run_integration


__all__ = [
    "run_integration", 
    "register_command_handler",
    "register_module_status_provider",
    "GetOrionEntityById",
    "PostCreateDeviceHeartbeatEntity",
    "GetFiwareDeviceById", 
    "PostDeviceHeartbeat",
    "PostNewVigiaDevice",
    "PostUpdateDeviceHeartbeatAttrs",
    "PostVigiaCommand",
    "PutVigiaDevice",
]
