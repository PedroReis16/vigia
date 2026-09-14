"""
Módulo de comandos para o FIWARE
"""

from multiprocessing.synchronize import Event as EventType

_stream_event: EventType | None = None


def init_stream_event(event: EventType) -> None:
    """
    Associa o Event compartilhado entre processos ao módulo.
    Deve ser chamado no início de cada processo filho.
    """
    global _stream_event
    _stream_event = event


def set_stream_status(status: bool) -> None:
    """
    Define o status de streaming do dispositivo
    """
    if _stream_event is None:
        raise RuntimeError("stream event não inicializado")

    if status:
        _stream_event.set()
    else:
        _stream_event.clear()


def get_stream_status() -> bool:
    """
    Busca o status de streaming do dispositivo
    """
    if _stream_event is None:
        return False

    return _stream_event.is_set()
