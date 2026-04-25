from dataclasses import dataclass


@dataclass
class VigiaCommand:
    name: str
    type: str = "command"
