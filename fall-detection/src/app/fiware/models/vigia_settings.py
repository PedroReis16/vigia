from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Any
from uuid import UUID, uuid4

from app.fiware.models.vigia_attributes import VigiaAttribute
from app.fiware.models.vigia_commands import VigiaCommand


def _parse_command(item: Any) -> VigiaCommand:
    if isinstance(item, VigiaCommand):
        return item
    if not isinstance(item, dict):
        return VigiaCommand(name=str(item))

    command_name = str(
        item.get("name") or item.get("command") or item.get("object_id") or ""
    ).strip()
    if not command_name:
        raise ValueError(f"Invalid command payload: {item}")
    return VigiaCommand(name=command_name, type=str(item.get("type", "command")))


def _parse_attribute(item: Any) -> VigiaAttribute:
    if isinstance(item, VigiaAttribute):
        return item
    if not isinstance(item, dict):
        raise ValueError(f"Invalid attribute payload: {item}")

    attr_name = str(item.get("name") or item.get("object_id") or "").strip()
    if not attr_name:
        raise ValueError(f"Invalid attribute name in payload: {item}")

    attr_type = str(item.get("type") or "Text")
    object_id = str(item.get("object_id") or item.get("name") or attr_name)
    return VigiaAttribute(name=attr_name, type=attr_type, object_id=object_id)


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
        object.__setattr__(self, "entity_name", f"urn:ngsi-ld:VigiaCam:{id_suffix}")

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> VigiaSettings:
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
            else [_parse_command(c) for c in commands_in]
        )

        attrs_in = data.get("attributes")
        attributes = (
            _default_attributes()
            if attrs_in is None
            else [_parse_attribute(a) for a in attrs_in]
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
        return cls._from_dict(json.loads(s))

    def to_dict(self) -> dict:
        data = asdict(self)
        data["device_id"] = str(data["device_id"])
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)
