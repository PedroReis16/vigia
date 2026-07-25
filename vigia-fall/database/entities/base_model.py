import uuid
from peewee import Model, UUIDField
from ..connection import db

class BaseModel(Model):
    """
    Modelo base para todas as entidades
    """

    id = UUIDField(primary_key=True, default=uuid.uuid4, index=True)

    class Meta:
        database = db