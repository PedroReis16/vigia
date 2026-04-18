from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Any
from uuid import UUID, uuid4

from app.integration.models.vigia_attributes import VigiaAttribute
from app.integration.models.vigia_commands import VigiaCommand


def _default_commands() -> list[VigiaCommand]:
    return [
        VigiaCommand(name="stream"),
        VigiaCommand(name="capture"),
        VigiaCommand(name="pose"),
    ]


def _default_attributes() -> list[VigiaAttribute]:
    return [
        VigiaAttribute(name="stream", type="Boolean", object_id="st"),
        VigiaAttribute(name="capture", type="Boolean", object_id="ca"),
        VigiaAttribute(name="pose", type="Boolean", object_id="po"),
    ]


@dataclass(frozen=True)
class VigiaSettings:
    device_id: UUID = field(default_factory=uuid4)
    entity_name: str = field(init=False)
    entity_type: str = "VigiaCam"
    protocol: str = "PDI-IoTA-UltraLight"
    transport: str = "MQTT"
    commands: list[VigiaCommand] = field(default_factory=_default_commands)
    attributes: list[VigiaAttribute] = field(default_factory=_default_attributes)

    def __post_init__(self) -> None:
        id_suffix = str(self.device_id).replace("-", "")[-4:]
        object.__setattr__(
            self, "entity_name", f"urn:ngsi-ld:VigiaCam:{id_suffix}"
        )

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> VigiaSettings:
        """Reconstrói a partir de JSON/`to_dict`; ignora `entity_name` (derivado de `device_id`)."""
        raw_id = data.get("device_id")
        if raw_id is None:
            device_id = uuid4()
        elif isinstance(raw_id, UUID):
            device_id = raw_id
        else:
            device_id = UUID(str(raw_id))

        commands_in = data.get("commands")
        commands = (
            _default_commands()
            if commands_in is None
            else [
                VigiaCommand(**c) if isinstance(c, dict) else c
                for c in commands_in
            ]
        )

        attrs_in = data.get("attributes")
        attributes = (
            _default_attributes()
            if attrs_in is None
            else [
                VigiaAttribute(**a) if isinstance(a, dict) else a
                for a in attrs_in
            ]
        )

        return cls(
            device_id=device_id,
            entity_type=data.get("entity_type", "VigiaCam"),
            protocol=data.get("protocol", "PDI-IoTA-UltraLight"),
            transport=data.get("transport", "MQTT"),
            commands=commands,
            attributes=attributes,
        )

    @classmethod
    def from_json(cls, s: str) -> VigiaSettings:
        """"
        Reconstrói a partir de JSON/`to_json`; ignora `entity_name` (derivado de `device_id`).
        """
        return cls._from_dict(json.loads(s))

    def to_dict(self) -> dict:
        """Dict JSON-serializável para `requests` (`json=`) e APIs."""
        data = asdict(self)
        data["device_id"] = str(data["device_id"])
        return data

    def to_json(self) -> str:
        """Representação JSON legível (debug/logs)."""
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)
