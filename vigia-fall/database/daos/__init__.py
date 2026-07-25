"""
DAOs do banco de dados
"""

from .device_dao import create_device, get_device

__all__ = [
    "create_device",
    "get_device",
]
