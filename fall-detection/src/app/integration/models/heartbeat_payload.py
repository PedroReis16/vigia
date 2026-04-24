from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HeartbeatPayload:
    entity_id: str
    entity_type: str
    heartbeat_at: str
    device_ip: str
    capture_status: str
    core_status: str

    def to_attrs_payload(self) -> dict:
        return {
            "heartbeatAt": {
                "type": "DateTime",
                "value": self.heartbeat_at,
            },
            "deviceIp": {
                "type": "Text",
                "value": self.device_ip,
            },
            "captureStatus": {
                "type": "Text",
                "value": self.capture_status,
            },
            "coreStatus": {
                "type": "Text",
                "value": self.core_status,
            },
        }

    def to_create_payload(self) -> dict:
        payload = self.to_attrs_payload()
        payload["id"] = self.entity_id
        payload["type"] = self.entity_type
        return payload

    @staticmethod
    def expected_schema() -> dict[str, str]:
        return {
            "heartbeatAt": "DateTime",
            "deviceIp": "Text",
            "captureStatus": "Text",
            "coreStatus": "Text",
        }
