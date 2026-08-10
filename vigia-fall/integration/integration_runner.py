"""
Módulo de runner para a integração do dispositivo com o serviço externo
"""

import asyncio
import json
from uuid import UUID

from shared import get_network_path, helpers_create_device_name, helpers_get_mac_address, get_identity_path
from database import create_database, get_device, create_device
from .device_ble import init_register_beacon
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import serialization

is_connected: bool = False


def __register_device() -> tuple[UUID, str, str]:
    """
    Registro das informações iniciais do dispositivo
    """

    device_name = helpers_create_device_name()
    mac_address = helpers_get_mac_address()

    tracked_device = get_device()

    if tracked_device:
        return tracked_device.id, tracked_device.name, tracked_device.mac_address

    device = create_device(device_name, mac_address)

    return device.id, device.name, device.mac_address


def __load_or_create_device_identity(
    device_id: UUID, device_name: str
) -> tuple[ed25519.Ed25519PrivateKey, x25519.X25519PrivateKey]:
    """
    Carrega ou cria as informações de identificação do dispositivo utilizado para a autenticação do dispositivo com o servidor
    """

    identity_path = get_identity_path()

    def __raw(k) -> str:
        return k.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ).hex()

    if identity_path.exists():
        data = json.loads(identity_path.read_text())

        sign_priv = ed25519.Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(data["sign_priv"])
        )
        ecdh_priv = x25519.X25519PrivateKey.from_private_bytes(
            bytes.fromhex(data["ecdh_priv"])
        )
        return sign_priv, ecdh_priv

    sign_priv = (
        ed25519.Ed25519PrivateKey.generate()
    )  # utilizada para assinar comandos/respostas do dispositivo
    ecdh_priv = (
        x25519.X25519PrivateKey.generate()
    )  # utilizada para derivar sessão no pareamento

    identity_path.parent.mkdir(parents=True, exist_ok=True)
    identity_path.write_text(
        json.dumps(
            {
                "device_id": str(device_id),
                "device_name": device_name,
                "sign_priv": __raw(sign_priv),
                "ecdh_priv": __raw(ecdh_priv),
            }
        )
    )

    identity_path.chmod(0o600)

    return sign_priv, ecdh_priv


async def initialize_device() -> None:
    """
    Inicialização dos dados de integração do dispositivo.
    O processo de inicialização somente é concluído após o dispositivo ter sido vinculado a um usuário
    """

    global is_connected  # pyright: ignore[reportGlobalVariable]
    is_connected = False

    create_database() # Cria o arquivo de banco de dados e atualiza as migrations do banco de dados

    if get_identity_path().exists() and get_network_path().exists():
        return
        
    device_id, device_name, mac_address = __register_device()
    sign_priv, ecdh_priv = __load_or_create_device_identity(device_id, device_name)

    await init_register_beacon(
        device_id, device_name, mac_address, sign_priv, ecdh_priv
    )

    while not is_connected:
        await asyncio.sleep(1)

    print("Device connected")
