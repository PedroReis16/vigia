"""
Módulo para o fluxo de integração da aplicação com o FIWARE
"""

from .runner import run_integration
from .requests.get_fiware_device_by_id import GetFiwareDeviceById
from .requests.post_new_vigia_device import PostNewVigiaDevice
from .requests.post_vigia_command import PostVigiaCommand


__all__ = [
    "run_integration", 
    "GetFiwareDeviceById", 
    "PostNewVigiaDevice",
    "PostVigiaCommand",
]
