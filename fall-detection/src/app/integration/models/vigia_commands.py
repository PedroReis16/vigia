from dataclasses import dataclass


@dataclass
class VigiaCommand:
    name: str
    command: str = "command"
