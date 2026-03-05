from src.ml import BaselineFallDetector
from src.replication import EventReplicator
from src.schemas import DetectionEvent, FrameInferenceRequest, FrameInferenceResponse
from src.vision import FeatureExtractor


class FallDetectionPipeline:
    def __init__(
        self,
        model: BaselineFallDetector,
        extractor: FeatureExtractor,
        replicator: EventReplicator,
    ) -> None:
        self._model = model
        self._extractor = extractor
        self._replicator = replicator

    async def run(self, request: FrameInferenceRequest) -> FrameInferenceResponse:
        features = self._extractor.from_vector(request.features)
        prediction = self._model.predict(features)

        event: DetectionEvent | None = None
        if prediction.fall_detected:
            event = DetectionEvent(
                camera_id=request.camera_id,
                confidence=prediction.confidence,
                metadata={"feature_count": len(features)},
            )
            await self._replicator.publish(event)

        return FrameInferenceResponse(
            fall_detected=prediction.fall_detected,
            confidence=prediction.confidence,
            event=event,
        )
