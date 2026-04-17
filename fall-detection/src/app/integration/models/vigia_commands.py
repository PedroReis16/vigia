from dataclasses import dataclass


@dataclass
class VigiaCommand:
    """Comando NGSI no IoT Agent: `name` + `type` (não `command`)."""

    name: str
    type: str = "command"
