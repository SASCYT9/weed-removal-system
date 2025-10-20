"""YOLOv8 weed detection module."""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


@dataclass
class Detection:
    """Detection result container."""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    center: Tuple[float, float]  # (cx, cy)


class YOLODetector:
    """YOLOv8 object detector for weed identification."""

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        input_size: Tuple[int, int] = (640, 640),
        class_names: List[str] = None
    ):
        """
        Initialize YOLO detector.

        Args:
            model_path: Path to YOLO model (.pt or .tflite)
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            input_size: Model input size (width, height)
            class_names: List of class names
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.input_size = input_size
        self.class_names = class_names or ["weed", "crop"]

        self.model = None
        self.is_tflite = model_path.endswith('.tflite')

        logger.info(f"Initializing YOLO detector with model: {model_path}")

    def load_model(self):
        """Load YOLO model."""
        try:
            if self.is_tflite:
                self._load_tflite_model()
            else:
                self._load_pytorch_model()

            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _load_tflite_model(self):
        """Load TensorFlow Lite model."""
        try:
            import tflite_runtime.interpreter as tflite
            logger.info("Using tflite_runtime")
        except ImportError:
            try:
                import tensorflow.lite as tflite
                logger.info("Using tensorflow.lite")
            except ImportError:
                raise ImportError(
                    "TensorFlow Lite not available. Install with: pip install tflite-runtime\n"
                    "Or use PyTorch model (.pt) instead by changing model_path in config.yaml"
                )

        self.interpreter = tflite.Interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()

        # Get input and output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        logger.info("TFLite model loaded")

    def _load_pytorch_model(self):
        """Load PyTorch YOLO model."""
        from ultralytics import YOLO

        self.model = YOLO(self.model_path)
        logger.info("PyTorch YOLO model loaded")

    def detect(self, image: np.ndarray) -> List[Detection]:
        """
        Detect objects in image.

        Args:
            image: Input image (RGB format)

        Returns:
            List of Detection objects
        """
        if self.model is None and not hasattr(self, 'interpreter'):
            logger.warning("Model not loaded, loading now...")
            self.load_model()

        try:
            if self.is_tflite:
                return self._detect_tflite(image)
            else:
                return self._detect_pytorch(image)

        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []

    def _detect_tflite(self, image: np.ndarray) -> List[Detection]:
        """
        Run detection using TFLite model.

        Args:
            image: Preprocessed input image

        Returns:
            List of detections
        """
        # Prepare input
        input_data = np.expand_dims(image, axis=0)

        # Set input tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)

        # Run inference
        self.interpreter.invoke()

        # Get output tensors
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        scores = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        class_ids = self.interpreter.get_tensor(self.output_details[2]['index'])[0]

        # Post-process detections
        detections = self._postprocess_detections(boxes, scores, class_ids)

        return detections

    def _detect_pytorch(self, image: np.ndarray) -> List[Detection]:
        """
        Run detection using PyTorch YOLO model.

        Args:
            image: Input image

        Returns:
            List of detections
        """
        # Run inference
        results = self.model(image, conf=self.confidence_threshold, iou=self.iou_threshold)

        detections = []
        for result in results:
            boxes = result.boxes

            for box in boxes:
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                # Get confidence and class
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])

                # Calculate center
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2

                # Create detection object
                detection = Detection(
                    class_id=class_id,
                    class_name=self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}",
                    confidence=confidence,
                    bbox=(float(x1), float(y1), float(x2), float(y2)),
                    center=(float(cx), float(cy))
                )
                detections.append(detection)

        logger.debug(f"Detected {len(detections)} objects")
        return detections

    def _postprocess_detections(
        self,
        boxes: np.ndarray,
        scores: np.ndarray,
        class_ids: np.ndarray
    ) -> List[Detection]:
        """
        Post-process raw detection outputs.

        Args:
            boxes: Bounding boxes
            scores: Confidence scores
            class_ids: Class IDs

        Returns:
            List of Detection objects
        """
        detections = []

        for i in range(len(scores)):
            if scores[i] >= self.confidence_threshold:
                x1, y1, x2, y2 = boxes[i]
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2

                class_id = int(class_ids[i])
                detection = Detection(
                    class_id=class_id,
                    class_name=self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}",
                    confidence=float(scores[i]),
                    bbox=(float(x1), float(y1), float(x2), float(y2)),
                    center=(float(cx), float(cy))
                )
                detections.append(detection)

        # Apply NMS
        detections = self._apply_nms(detections)

        logger.debug(f"Post-processed {len(detections)} detections")
        return detections

    def _apply_nms(self, detections: List[Detection]) -> List[Detection]:
        """
        Apply Non-Maximum Suppression to remove overlapping boxes.

        Args:
            detections: List of detections

        Returns:
            Filtered list of detections
        """
        if len(detections) == 0:
            return []

        # Convert to numpy arrays
        boxes = np.array([d.bbox for d in detections])
        scores = np.array([d.confidence for d in detections])

        # Get NMS indices
        indices = self._nms(boxes, scores, self.iou_threshold)

        # Filter detections
        filtered_detections = [detections[i] for i in indices]

        return filtered_detections

    @staticmethod
    def _nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> List[int]:
        """
        Non-Maximum Suppression implementation.

        Args:
            boxes: Bounding boxes (N, 4) in format (x1, y1, x2, y2)
            scores: Confidence scores (N,)
            iou_threshold: IoU threshold

        Returns:
            List of indices to keep
        """
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]

        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]

        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h

            iou = inter / (areas[i] + areas[order[1:]] - inter)

            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]

        return keep

    def filter_by_class(self, detections: List[Detection], class_name: str) -> List[Detection]:
        """
        Filter detections by class name.

        Args:
            detections: List of detections
            class_name: Class name to filter

        Returns:
            Filtered detections
        """
        return [d for d in detections if d.class_name == class_name]

    def get_weed_detections(self, detections: List[Detection]) -> List[Detection]:
        """
        Get only weed detections.

        Args:
            detections: List of all detections

        Returns:
            List of weed detections
        """
        return self.filter_by_class(detections, "weed")
