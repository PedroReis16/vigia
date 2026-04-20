"""Uma pessoa rastreada e os keypoints válidos num frame."""

from __future__ import annotations

from app.capture.pose.body_data import BodyData


class PersonData:  # pylint: disable=too-few-public-methods
    """Uma pessoa rastreada e a lista de keypoints válidos neste frame."""

    def __init__(self, person_id: int, body_data: list[BodyData]) -> None:
        self.person_id = person_id
        self.body_data = body_data
