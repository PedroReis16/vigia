"""
DAOs do banco de dados
"""

from .device_dao import (
    create_device,
    get_device_details,
    update_device_group,
    delete_device_group,
)

__all__ = [
    "create_device",
    "get_device_details",
    "update_device_group",
    "delete_device_group",
]
