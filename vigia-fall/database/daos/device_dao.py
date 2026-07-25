"""
Módulo para operações de banco de dados relacionadas a dispositivos
"""

import datetime
from typing import Optional
from uuid import UUID
from models import EntityValidationException

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

        device = Device.create(name=name, mac_address=mac_address)

        return device
    finally:
        db.close()


def get_device_details() -> Optional[Device]:
    """
    Retorna os detalhes do dispositivo registrado
    """

    try:
        db.connect()

        devices = Device.select()

        if not devices:
            return None

        device = devices[0]

        return device
    finally:
        db.close()


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

    finally:
        db.close()
