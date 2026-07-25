"""
Módulo para operações de banco de dados relacionadas a dispositivos
"""

import datetime
from functools import lru_cache
from typing import Optional
from uuid import UUID
from shared import EntityValidationException

from ..entities import Device
from ..connection import db


def create_device(name: str, mac_address: str) -> Device:
    """
    Registro de um novo dispositivo
    """

    try:
        db.connect()

        devices = Device.select()

        if devices:
            raise EntityValidationException("Dispositivo já registrado")

        device = Device.create(
            name=name,
            mac_address=mac_address,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        return device
    finally:
        db.close()


def __get_device_details() -> Optional[Device]:
    """
    Retorna os detalhes do dispositivo registrado (sempre consulta o banco)
    """

    try:
        db.connect()

        devices = Device.select()

        if not devices:
            return None

        return devices[0]
    finally:
        db.close()


@lru_cache
def get_device() -> Optional[Device]:
    """
    Retorna o dispositivo registrado, priorizando o cache da aplicação
    """

    return __get_device_details()


def update_device_group(group_id: UUID) -> None:
    """
    Vincula o dispositivo a um grupo de usuários
    """

    try:
        db.connect()

        devices = Device.select()

        if not devices:
            raise EntityValidationException("Nenhum dispositivo registrado")

        device = devices[0]

        device.group_id = group_id
        device.updated_at = datetime.datetime.now()

        device.save()

        get_device.cache_clear()

    finally:
        db.close()


def delete_device_group() -> None:
    """
    Desvincula o dispositivo de um grupo de usuários
    """

    try:
        db.connect()

        devices = Device.select()

        if not devices:
            raise EntityValidationException("Nenhum dispositivo registrado")

        device = devices[0]

        device.group_id = None
        device.updated_at = datetime.datetime.now()

        device.save()

        get_device.cache_clear()

    finally:
        db.close()
