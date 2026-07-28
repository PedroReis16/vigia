"""
Módulo de conexão com o banco de dados da aplicação
"""

from .database import create_database
from .entities import Device

from . import daos
from .daos import *

__all__ = ["create_database", "Device", *daos.__all__]
