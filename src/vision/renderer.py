"""Frame renderer for YOLO detection results with non-overlapping labels."""

import cv2
import numpy as np
from ultralytics.engine.results import Results


class DetectionRenderer:
    """Renders YOLO detection results on frames with optimized label placement."""

    def __init__(
        self,
        font: int = cv2.FONT_HERSHEY_SIMPLEX,
        font_scale: float = 0.5,
        thickness: int = 1,
        padding: int = 6,
        line_gap: int = 4,
        show_labels: bool = False,
        show_conf: bool = False,
    ) -> None:
        """Initialize renderer with display settings.
        
        Args:
            font: OpenCV font type
            font_scale: Font size scale
            thickness: Text line thickness
            padding: Padding around text in label box
            line_gap: Gap between multiple text lines
            show_labels: Show built-in YOLO labels
            show_conf: Show built-in YOLO confidence
        """
        self.font = font
        self.font_scale = font_scale
        self.thickness = thickness
        self.padding = padding
        self.line_gap = line_gap
        self.show_labels = show_labels
        self.show_conf = show_conf

    def render(self, results: list[Results]) -> np.ndarray | None:
        """Render detection results on frame.
        
        Args:
            results: YOLO detection results
            
        Returns:
            Annotated frame or None if no results
        """
        if not results:
            return None

        # Get first result (single frame prediction)
        result = results[0]
        
        # Start with YOLO's annotated frame (with boxes, keypoints, etc.)
        annotated_frame = result.plot(labels=self.show_labels, conf=self.show_conf)

        # If no boxes detected, return annotated frame as is
        if result.boxes is None or len(result.boxes) == 0:
            return annotated_frame

        # Add custom information labels with non-overlapping placement
        self._add_custom_labels(annotated_frame, result)

        return annotated_frame

    def _add_custom_labels(self, frame: np.ndarray, result: Results) -> None:
        """Add custom labels to frame with non-overlapping placement.
        
        Args:
            frame: Frame to annotate (modified in place)
            result: YOLO detection result
        """
        frame_height, frame_width = frame.shape[:2]
        occupied_regions: list[tuple[int, int, int, int]] = []

        for i, box in enumerate(result.boxes):
            conf = float(box.conf[0].item())
            cls = int(box.cls[0].item())
            class_name = result.names[cls]

            # Get bounding box coordinates
            x1, y1, _, _ = map(int, box.xyxy[0])

            # Create label text
            label_lines = [f"Classe: {class_name} ID: {i} Conf: {conf:.2f}"]

            # Calculate label dimensions
            label_width, label_height = self._calculate_label_size(label_lines)

            # Find non-overlapping position for label
            label_x, label_y = self._find_label_position(
                x1, y1, label_width, label_height,
                frame_width, frame_height, occupied_regions
            )

            # Track occupied region
            occupied_regions.append((label_x, label_y, label_x + label_width, label_y + label_height))

            # Draw label background
            cv2.rectangle(
                frame,
                (label_x, label_y),
                (label_x + label_width, label_y + label_height),
                (0, 255, 0),
                -1,
            )

            # Draw label text
            self._draw_label_text(frame, label_lines, label_x, label_y)

    def _calculate_label_size(self, label_lines: list[str]) -> tuple[int, int]:
        """Calculate required size for label box.
        
        Args:
            label_lines: List of text lines to display
            
        Returns:
            Tuple of (width, height) in pixels
        """
        text_sizes = [
            cv2.getTextSize(line, self.font, self.font_scale, self.thickness)[0]
            for line in label_lines
        ]
        
        text_width = max(size[0] for size in text_sizes)
        line_height = max(size[1] for size in text_sizes)

        label_width = text_width + (self.padding * 2)
        label_height = (line_height * len(label_lines)) + \
                      (self.line_gap * (len(label_lines) - 1)) + \
                      (self.padding * 2)

        return label_width, label_height

    def _find_label_position(
        self,
        x1: int,
        y1: int,
        label_width: int,
        label_height: int,
        frame_width: int,
        frame_height: int,
        occupied_regions: list[tuple[int, int, int, int]],
    ) -> tuple[int, int]:
        """Find non-overlapping position for label.
        
        Args:
            x1, y1: Bounding box top-left coordinates
            label_width, label_height: Label dimensions
            frame_width, frame_height: Frame dimensions
            occupied_regions: List of already occupied regions [(x1, y1, x2, y2), ...]
            
        Returns:
            Tuple of (x, y) coordinates for label top-left corner
        """
        # Start with position above bounding box
        label_x = max(0, min(x1, frame_width - label_width))
        label_y = max(0, y1 - label_height - 8)

        # If label goes off top of frame, place below bounding box instead
        if label_y < 0:
            label_y = min(y1 + 8, frame_height - label_height)

        # Check for overlaps and adjust position
        max_iterations = 10
        iteration = 0
        while iteration < max_iterations and self._has_overlap(
            label_x, label_y, label_width, label_height, occupied_regions
        ):
            label_y += label_height + 6
            # If we've gone too far down, reset to top
            if label_y + label_height >= frame_height:
                label_y = max(0, y1 - label_height - 8)
                break
            iteration += 1

        return label_x, label_y

    def _has_overlap(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        regions: list[tuple[int, int, int, int]],
    ) -> bool:
        """Check if position overlaps with any occupied region.
        
        Args:
            x, y: Top-left coordinates
            width, height: Box dimensions
            regions: List of occupied regions [(x1, y1, x2, y2), ...]
            
        Returns:
            True if overlap detected, False otherwise
        """
        x2 = x + width
        y2 = y + height

        for rx1, ry1, rx2, ry2 in regions:
            if x < rx2 and x2 > rx1 and y < ry2 and y2 > ry1:
                return True

        return False

    def _draw_label_text(
        self,
        frame: np.ndarray,
        label_lines: list[str],
        label_x: int,
        label_y: int,
    ) -> None:
        """Draw text lines on frame.
        
        Args:
            frame: Frame to draw on (modified in place)
            label_lines: List of text lines to draw
            label_x, label_y: Top-left position of label box
        """
        text_sizes = [
            cv2.getTextSize(line, self.font, self.font_scale, self.thickness)[0]
            for line in label_lines
        ]
        line_height = max(size[1] for size in text_sizes)

        text_y = label_y + self.padding + line_height

        for line in label_lines:
            cv2.putText(
                frame,
                line,
                (label_x + self.padding, text_y),
                self.font,
                self.font_scale,
                (0, 0, 0),  # Black text
                self.thickness,
                lineType=cv2.LINE_AA,
            )
            text_y += line_height + self.line_gap
