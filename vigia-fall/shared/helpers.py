"""
Módulo de helpers para o sistema
"""

from uuid import uuid4
from getmac import get_mac_address


def helpers_convert_to_bool(value:str) -> bool:
    """
    Converte uma string para um booleano
    """
    v=value.strip().lower()
    return v in ("1", "true", "t", "yes", "y")


def helpers_create_device_name() -> str:
    """
    Criação do nome do dispositivo
    """
    return f"Vigia-{uuid4().hex[:8]}"

def helpers_get_mac_address() -> str:
    """
    Retorna o endereço MAC do dispositivo principal
    """
    main_mac = get_mac_address() # Retorna o endereço MAC do dispositivo principal
    return main_mac
