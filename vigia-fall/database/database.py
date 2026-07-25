"""
Módulo central para inicialização das conexões com o banco de dados
"""

import os
from shared import get_settings

from .connection import db
from .entities import Device


def __resolve_database_path() -> str:
    data_dir = get_settings().data_dir

    if not data_dir:
        raise ValueError("DATA_DIR não configurado")

    db_dir = os.path.join(data_dir, "DB")

    os.makedirs(db_dir, exist_ok=True)

    return os.path.join(db_dir, "vigia.db")


def create_database() -> None:
    """
    Cria o banco de dados e as tabelas necessárias
    """
    try:
        db.init(__resolve_database_path())

        db.connect()
        db.create_tables([Device])

        db.close()
    except Exception as e:
        raise e
