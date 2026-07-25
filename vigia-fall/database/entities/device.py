"""
Entidade para armazenamento das configurações do dispositivo
"""

import datetime
from peewee import CharField, DateTimeField, UUIDField
from .base_model import BaseModel


class Device(BaseModel):
    """
    Modelo para armazenamento dos detalhes do dispositivo
    """

    name = CharField(unique=True, index=True)
    group_id = UUIDField(null=True, index=True)
    mac_address = CharField()
    created_at = DateTimeField(default=datetime.datetime.now, index=True)
    updated_at = DateTimeField(null=True)
