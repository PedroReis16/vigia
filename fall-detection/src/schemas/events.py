from datetime import datetime, timezone

from pydantic import BaseModel, Field


class FrameInferenceRequest(BaseModel):
    camera_id: str = Field(..., examples=["cam-01"])
    features: list[float] = Field(
        default_factory=list,
        description="Vetor numérico extraído de um frame para inferência.",
    )


class DetectionEvent(BaseModel):
    event_type: str = Field(default="fall.detected")
    camera_id: str
    confidence: float
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, str | float | int | bool] = Field(default_factory=dict)


class FrameInferenceResponse(BaseModel):
    fall_detected: bool
    confidence: float
    event: DetectionEvent | None = None
