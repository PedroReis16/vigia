from dataclasses import asdict, dataclass, field
import json
from uuid import UUID, uuid4

from app.integration.models.vigia_attributes import VigiaAttribute
from app.integration.models.vigia_commands import VigiaCommand


@dataclass(frozen=True)
class VigiaSettings:
    device_id: UUID = field(default_factory=uuid4)
    entity_name: str = field(init=False)
    entity_type: str = "VigiaCam"
    protocol: str = "PDI-IoTA-UltraLight"
    transport: str = "MQTT"
    commands: list[VigiaCommand] = field(default_factory=lambda: [
        VigiaCommand(name="stream"),
        VigiaCommand(name="capture"),
        VigiaCommand(name="pose"),
    ])
    attributes: list[VigiaAttribute] = field(default_factory=lambda: [
        VigiaAttribute(name="stream", type="Boolean", object_id="st"),
        VigiaAttribute(name="capture", type="Boolean", object_id="ca"),
        VigiaAttribute(name="pose", type="Boolean", object_id="po"),
    ])

    def __post_init__(self) -> None:
        id_suffix = str(self.device_id).replace("-", "")[-4:]
        object.__setattr__(
            self, "entity_name", f"urn:ngsi-ld:VigiaCam:{id_suffix}"
        )


    def to_dict(self) -> dict:
        """Dict JSON-serializável para `requests` (`json=`) e APIs."""
        data = asdict(self)
        data["device_id"] = str(data["device_id"])
        return data

    def to_json(self) -> str:
        """Representação JSON legível (debug/logs)."""
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)
