from dataclasses import dataclass


@dataclass
class VigiaAttribute:
    name: str
    type: str
    object_id: str