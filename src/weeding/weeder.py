"""Weeding mechanism controller."""

import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO for development
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode): pass
        @staticmethod
        def output(pin, state): pass
        @staticmethod
        def cleanup(): pass

    GPIO = MockGPIO()

from typing import List, Tuple
from dataclasses import dataclass
from ..detection.yolo_detector import Detection
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


@dataclass
class WeedingAction:
    """Weeding action record."""
    timestamp: float
    weed_position: Tuple[float, float]
    robot_position: Tuple[float, float]
    confidence: float
    success: bool


class Weeder:
    """Weeding mechanism controller."""

    def __init__(
        self,
        mechanism_pin: int = 22,
        activation_duration: float = 0.5,
        offset_x: float = 0.0,
        offset_y: float = 0.2,
        min_confidence: float = 0.6
    ):
        """
        Initialize weeder.

        Args:
            mechanism_pin: GPIO pin for weeding mechanism
            activation_duration: How long to activate mechanism (seconds)
            offset_x: X offset from camera to mechanism (meters)
            offset_y: Y offset from camera to mechanism (meters)
            min_confidence: Minimum detection confidence to trigger weeding
        """
        self.mechanism_pin = mechanism_pin
        self.activation_duration = activation_duration
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.min_confidence = min_confidence

        self._initialized = False
        self._active = False
        self.weeding_history = []

        logger.info(
            f"Weeder initialized: pin={mechanism_pin}, "
            f"duration={activation_duration}s, offset=({offset_x}, {offset_y})"
        )

    def setup(self):
        """Setup GPIO for weeding mechanism."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.mechanism_pin, GPIO.OUT)
            GPIO.output(self.mechanism_pin, GPIO.LOW)

            self._initialized = True
            logger.info("Weeder setup complete")

        except Exception as e:
            logger.error(f"Failed to setup weeder: {e}")
            raise

    def activate(self, weed_position: Tuple[float, float] = None, robot_position: Tuple[float, float] = None):
        """
        Activate weeding mechanism.

        Args:
            weed_position: Position of weed in image/world coordinates
            robot_position: Current robot position
        """
        if not self._initialized:
            logger.warning("Weeder not initialized")
            return

        try:
            logger.info(f"Activating weeding mechanism at position {weed_position}")

            # Activate mechanism
            GPIO.output(self.mechanism_pin, GPIO.HIGH)
            self._active = True

            # Wait for activation duration
            time.sleep(self.activation_duration)

            # Deactivate mechanism
            GPIO.output(self.mechanism_pin, GPIO.LOW)
            self._active = False

            # Record weeding action
            action = WeedingAction(
                timestamp=time.time(),
                weed_position=weed_position if weed_position else (0, 0),
                robot_position=robot_position if robot_position else (0, 0),
                confidence=1.0,
                success=True
            )
            self.weeding_history.append(action)

            logger.info("Weeding activation complete")

        except Exception as e:
            logger.error(f"Error activating weeder: {e}")
            self._active = False

    def process_detections(
        self,
        detections: List[Detection],
        robot_position: Tuple[float, float] = None,
        camera_to_world_transform: callable = None
    ):
        """
        Process detections and activate weeder if needed.

        Args:
            detections: List of weed detections
            robot_position: Current robot position
            camera_to_world_transform: Function to transform camera coords to world coords
        """
        # Filter for high-confidence weed detections
        weeds = [d for d in detections if d.class_name == "weed" and d.confidence >= self.min_confidence]

        if len(weeds) == 0:
            return

        logger.info(f"Processing {len(weeds)} weed detections")

        for weed in weeds:
            # Get weed position in camera frame
            camera_x, camera_y = weed.center

            # Transform to world coordinates if transform provided
            if camera_to_world_transform:
                world_x, world_y = camera_to_world_transform(camera_x, camera_y)
            else:
                world_x, world_y = camera_x, camera_y

            # Apply mechanism offset
            target_x = world_x + self.offset_x
            target_y = world_y + self.offset_y

            # Check if weed is in range for weeding
            if self._is_in_range(target_x, target_y):
                self.activate(
                    weed_position=(target_x, target_y),
                    robot_position=robot_position
                )

    def _is_in_range(self, x: float, y: float, max_range: float = 0.5) -> bool:
        """
        Check if position is within weeding range.

        Args:
            x: X coordinate
            y: Y coordinate
            max_range: Maximum range in meters

        Returns:
            True if in range
        """
        distance = (x**2 + y**2) ** 0.5
        return distance <= max_range

    def emergency_stop(self):
        """Emergency stop - immediately deactivate mechanism."""
        if self._initialized:
            GPIO.output(self.mechanism_pin, GPIO.LOW)
            self._active = False
            logger.warning("Weeder emergency stop activated")

    def is_active(self) -> bool:
        """Check if weeder is currently active."""
        return self._active

    def get_statistics(self) -> dict:
        """
        Get weeding statistics.

        Returns:
            Dictionary with statistics
        """
        total_actions = len(self.weeding_history)
        successful_actions = sum(1 for a in self.weeding_history if a.success)

        return {
            'total_actions': total_actions,
            'successful_actions': successful_actions,
            'success_rate': successful_actions / total_actions if total_actions > 0 else 0.0,
            'last_action_time': self.weeding_history[-1].timestamp if self.weeding_history else None
        }

    def clear_history(self):
        """Clear weeding history."""
        self.weeding_history.clear()
        logger.info("Weeding history cleared")

    def cleanup(self):
        """Cleanup GPIO resources."""
        if self._initialized:
            self.emergency_stop()
            GPIO.cleanup()
            self._initialized = False
            logger.info("Weeder cleaned up")

    def __enter__(self):
        """Context manager entry."""
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


class MockWeeder(Weeder):
    """Mock weeder for development/testing without hardware."""

    def __init__(self, *args, **kwargs):
        """Initialize mock weeder."""
        super().__init__(*args, **kwargs)
        self.activation_count = 0
        logger.info("🔧 Mock Weeder initialized (simulated mechanism)")

    def setup(self):
        """Mock setup - no GPIO needed."""
        self._initialized = True
        logger.info("🔧 Mock weeder setup complete")

    def activate(self, weed_position: Tuple[float, float] = None, robot_position: Tuple[float, float] = None):
        """Simulate weeding mechanism activation."""
        if not self._initialized:
            logger.warning("Weeder not initialized")
            return

        self.activation_count += 1
        logger.info(f"🔧 Mock weeder activated #{self.activation_count} at position {weed_position}")

        # Simulate activation time
        time.sleep(self.activation_duration)

        # Record action
        action = WeedingAction(
            timestamp=time.time(),
            weed_position=weed_position if weed_position else (0, 0),
            robot_position=robot_position if robot_position else (0, 0),
            confidence=1.0,
            success=True
        )
        self.weeding_history.append(action)

        logger.info(f"🔧 Mock weeding complete (total: {self.activation_count})")

    def emergency_stop(self):
        """Simulate emergency stop."""
        self._active = False
        logger.warning("🔧 Mock weeder emergency stop activated")

    def cleanup(self):
        """Mock cleanup - no GPIO to clean."""
        self._initialized = False
        logger.info(f"🔧 Mock weeder cleaned up (total activations: {self.activation_count})")
