"""Cliente MQTT fake para testes de integração (sem broker real)."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any, Callable, ClassVar


class FakeMQTTMessage:
    __slots__ = ("payload",)

    def __init__(self, payload: bytes) -> None:
        self.payload = payload


class FakeReasonCode:
    __slots__ = ("is_failure",)

    def __init__(self, *, failure: bool = False) -> None:
        self.is_failure = failure


class FakeMQTTClient:
    """Substitui `mqtt.Client`: em `loop_start` agenda on_connect + on_message(s)."""

    queued_payloads: ClassVar[list[bytes]] = []
    after_emit: ClassVar[Callable[[], None] | None] = None

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self.on_connect: Callable[..., None] | None = None
        self.on_message: Callable[..., None] | None = None

    @classmethod
    def reset(cls, payloads: list[bytes], after_emit: Callable[[], None] | None = None) -> None:
        cls.queued_payloads = payloads
        cls.after_emit = after_emit

    def username_pw_set(self, *_a: Any, **_k: Any) -> None:
        return None

    def tls_set_context(self, *_a: Any, **_k: Any) -> None:
        return None

    def connect(self, *_a: Any, **_k: Any) -> None:
        return None

    def subscribe(self, *_a: Any, **_k: Any) -> tuple[int, int | None]:
        """Paho retorna (result, mid); o listener ignora o retorno."""
        return (0, None)

    def loop_start(self) -> None:
        loop = asyncio.get_running_loop()

        def emit_sequence() -> None:
            if self.on_connect is not None:
                rc = FakeReasonCode(failure=False)
                flags = SimpleNamespace()
                self.on_connect(self, None, flags, rc)
            if self.on_message is not None:
                for raw in type(self).queued_payloads:
                    self.on_message(self, None, FakeMQTTMessage(raw))
            if type(self).after_emit is not None:
                type(self).after_emit()

        loop.call_soon(emit_sequence)

    def loop_stop(self) -> None:
        return None

    def disconnect(self) -> None:
        return None


def fiware_command_payload(command: str, extra: dict | None = None) -> bytes:
    """JSON estilo comando remoto (campo `command`)."""
    body: dict[str, Any] = {"command": command}
    if extra:
        body.update(extra)
    return json.dumps(body).encode("utf-8")


def fiware_name_payload(name: str) -> bytes:
    """JSON usando `name` em vez de `command` (IoT Agent / NGSI variante)."""
    return json.dumps({"name": name}).encode("utf-8")
