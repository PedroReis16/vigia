"""
Modelos de dados válidos para o sistema de integração com o FIWARE
"""

from app.integration.models.vigia_commands import VigiaCommand
from app.integration.models.vigia_settings import VigiaSettings

__all__ = [
    "VigiaCommand",
    "VigiaSettings",
    "VigiaAttribute",
]