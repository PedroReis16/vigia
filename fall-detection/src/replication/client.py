import logging
from datetime import datetime, timezone

import httpx

from src.schemas import DetectionEvent

logger = logging.getLogger(__name__)


class EventReplicator:
    def __init__(
        self,
        enabled: bool,
        target_urls: list[str],
        timeout_seconds: float = 2.0,
        auth_token: str | None = None,
    ) -> None:
        self._target_urls = [url for url in target_urls if url]
        self._enabled = enabled and bool(self._target_urls)
        self._timeout_seconds = timeout_seconds
        self._auth_token = auth_token
        self._local_events: list[DetectionEvent] = []
        self._delivery_attempts: list[dict[str, str | int | bool | None]] = []

    async def publish(self, event: DetectionEvent) -> None:
        self._local_events.append(event)

        if not self._enabled:
            return

        payload = event.model_dump(mode="json")
        headers = (
            {"Authorization": f"Bearer {self._auth_token}"}
            if self._auth_token
            else None
        )

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            for target_url in self._target_urls:
                await self._publish_to_target(
                    client=client,
                    target_url=target_url,
                    payload=payload,
                    headers=headers,
                    event_type=event.event_type,
                )

    def last_events(self, limit: int = 20) -> list[DetectionEvent]:
        return self._local_events[-limit:]

    def last_deliveries(self, limit: int = 50) -> list[dict[str, str | int | bool | None]]:
        return self._delivery_attempts[-limit:]

    def configured_targets(self) -> list[str]:
        return list(self._target_urls)

    async def _publish_to_target(
        self,
        client: httpx.AsyncClient,
        target_url: str,
        payload: dict,
        headers: dict[str, str] | None,
        event_type: str,
    ) -> None:
        attempt: dict[str, str | int | bool | None] = {
            "target_url": target_url,
            "event_type": event_type,
            "success": False,
            "status_code": None,
            "error": None,
            "attempted_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            response = await client.post(target_url, json=payload, headers=headers)
            attempt["status_code"] = response.status_code
            response.raise_for_status()
            attempt["success"] = True
        except httpx.HTTPError as error:
            attempt["error"] = str(error)
            logger.warning("Falha ao replicar evento para %s: %s", target_url, error)

        self._delivery_attempts.append(attempt)
