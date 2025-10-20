"""Tests for detection module."""

import pytest
import numpy as np
from src.detection.yolo_detector import YOLODetector, Detection


class TestYOLODetector:
    """Test YOLODetector class."""

    def test_init(self):
        """Test detector initialization."""
        detector = YOLODetector(
            model_path="models/yolov8n.tflite",
            confidence_threshold=0.5,
            iou_threshold=0.45,
            class_names=["weed", "crop"]
        )

        assert detector.confidence_threshold == 0.5
        assert detector.iou_threshold == 0.45
        assert detector.class_names == ["weed", "crop"]

    def test_nms(self):
        """Test Non-Maximum Suppression."""
        # Create overlapping boxes
        boxes = np.array([
            [10, 10, 50, 50],
            [15, 15, 55, 55],
            [100, 100, 150, 150]
        ])
        scores = np.array([0.9, 0.8, 0.95])

        # Apply NMS
        indices = YOLODetector._nms(boxes, scores, iou_threshold=0.5)

        # Should keep first and third box
        assert len(indices) == 2
        assert 0 in indices
        assert 2 in indices

    def test_filter_by_class(self):
        """Test filtering detections by class."""
        detector = YOLODetector(
            model_path="models/test.tflite",
            class_names=["weed", "crop"]
        )

        # Create test detections
        detections = [
            Detection(0, "weed", 0.9, (10, 10, 50, 50), (30, 30)),
            Detection(1, "crop", 0.8, (60, 60, 100, 100), (80, 80)),
            Detection(0, "weed", 0.7, (120, 120, 160, 160), (140, 140))
        ]

        # Filter weeds
        weeds = detector.filter_by_class(detections, "weed")

        assert len(weeds) == 2
        assert all(d.class_name == "weed" for d in weeds)


class TestDetection:
    """Test Detection dataclass."""

    def test_detection_creation(self):
        """Test detection object creation."""
        detection = Detection(
            class_id=0,
            class_name="weed",
            confidence=0.95,
            bbox=(10, 10, 50, 50),
            center=(30, 30)
        )

        assert detection.class_id == 0
        assert detection.class_name == "weed"
        assert detection.confidence == 0.95
        assert detection.bbox == (10, 10, 50, 50)
        assert detection.center == (30, 30)


if __name__ == "__main__":
    pytest.main([__file__])
