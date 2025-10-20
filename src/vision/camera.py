"""Camera capture module using PiCamera2."""

import numpy as np
from picamera2 import Picamera2
from picamera2.configuration import CameraConfiguration
from typing import Tuple, Optional
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class Camera:
    """Raspberry Pi camera interface using PiCamera2."""

    def __init__(
        self,
        resolution: Tuple[int, int] = (1920, 1080),
        framerate: int = 30,
        format: str = "RGB888"
    ):
        """
        Initialize camera.

        Args:
            resolution: Camera resolution (width, height)
            framerate: Frames per second
            format: Pixel format (RGB888, YUV420, etc.)
        """
        self.resolution = resolution
        self.framerate = framerate
        self.format = format
        self.camera = None
        self._is_running = False

        logger.info(f"Initializing camera with resolution {resolution} at {framerate} fps")

    def start(self):
        """Start camera capture."""
        try:
            self.camera = Picamera2()

            # Configure camera
            config = self.camera.create_still_configuration(
                main={"size": self.resolution, "format": self.format},
                buffer_count=2
            )
            self.camera.configure(config)

            # Start camera
            self.camera.start()
            self._is_running = True

            logger.info("Camera started successfully")

        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            raise

    def capture(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from camera.

        Returns:
            numpy array with shape (height, width, channels) or None if capture fails
        """
        if not self._is_running:
            logger.warning("Camera not started, call start() first")
            return None

        try:
            # Capture array directly
            frame = self.camera.capture_array()
            return frame

        except Exception as e:
            logger.error(f"Failed to capture frame: {e}")
            return None

    def capture_continuous(self):
        """
        Generator for continuous frame capture.

        Yields:
            numpy array frames
        """
        if not self._is_running:
            self.start()

        while self._is_running:
            frame = self.capture()
            if frame is not None:
                yield frame

    def stop(self):
        """Stop camera capture and release resources."""
        if self.camera and self._is_running:
            try:
                self.camera.stop()
                self.camera.close()
                self._is_running = False
                logger.info("Camera stopped")
            except Exception as e:
                logger.error(f"Error stopping camera: {e}")

    def is_running(self) -> bool:
        """Check if camera is running."""
        return self._is_running

    def get_properties(self) -> dict:
        """
        Get camera properties.

        Returns:
            Dictionary with camera properties
        """
        return {
            "resolution": self.resolution,
            "framerate": self.framerate,
            "format": self.format,
            "is_running": self._is_running
        }

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
