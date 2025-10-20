"""Camera capture module with support for multiple sources."""

import numpy as np
import cv2
import time
from typing import Tuple, Optional, Union
from pathlib import Path
import urllib.request

# Try to import PiCamera2 (only available on Raspberry Pi)
try:
    from picamera2 import Picamera2
    from picamera2.configuration import CameraConfiguration
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False

from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)

class Camera:
    """Multi-source camera interface supporting PiCamera2, Webcam, IP Camera, and files."""

    def __init__(
        self,
        resolution: Tuple[int, int] = (1920, 1080),
        framerate: int = 30,
        format: str = "RGB888",
        source: str = "picamera",
        webcam_index: int = 0,
        ip_camera_url: str = None,
        video_file: str = None,
        images_folder: str = None
    ):
        """
        Initialize camera with flexible source support.

        Args:
            resolution: Camera resolution (width, height)
            framerate: Frames per second
            format: Pixel format (RGB888, YUV420, etc.)
            source: Camera source - "picamera", "webcam", "ip_camera", "video_file", "images"
            webcam_index: Index of webcam (0 for default)
            ip_camera_url: URL for IP camera stream (e.g., IP Webcam app)
            video_file: Path to video file for testing
            images_folder: Path to folder with test images
        """
        self.resolution = resolution
        self.framerate = framerate
        self.format = format
        self.source = source
        self.webcam_index = webcam_index
        self.ip_camera_url = ip_camera_url
        self.video_file = video_file
        self.images_folder = images_folder
        
        self.camera = None
        self.cap = None  # OpenCV VideoCapture
        self.image_files = []
        self.current_image_idx = 0
        self._is_running = False

        logger.info(f"Initializing camera with source '{source}' at resolution {resolution}")

    def start(self):
        """Start camera capture based on selected source."""
        try:
            if self.source == "picamera":
                self._start_picamera()
            elif self.source == "webcam":
                self._start_webcam()
            elif self.source == "ip_camera":
                self._start_ip_camera()
            elif self.source == "video_file":
                self._start_video_file()
            elif self.source == "images":
                self._start_images()
            else:
                raise ValueError(f"Unknown camera source: {self.source}")

            self._is_running = True
            logger.info(f"Camera started successfully (source: {self.source})")

        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            raise

    def _start_picamera(self):
        """Start Raspberry Pi Camera."""
        if not PICAMERA_AVAILABLE:
            raise RuntimeError("PiCamera2 not available. Install picamera2 or use development mode.")

        self.camera = Picamera2()
        config = self.camera.create_still_configuration(
            main={"size": self.resolution, "format": self.format},
            buffer_count=2
        )
        self.camera.configure(config)
        self.camera.start()
        logger.info("PiCamera2 started")

    def _start_webcam(self):
        """Start webcam using OpenCV."""
        self.cap = cv2.VideoCapture(self.webcam_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open webcam {self.webcam_index}")

        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, self.framerate)

        # Verify settings
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(f"Webcam started: {actual_width}x{actual_height}")

    def _start_ip_camera(self):
        """Start IP camera stream (e.g., smartphone camera via IP Webcam app)."""
        if not self.ip_camera_url:
            raise ValueError("IP camera URL not provided")

        # Try to connect
        self.cap = cv2.VideoCapture(self.ip_camera_url)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not connect to IP camera: {self.ip_camera_url}")

        logger.info(f"IP camera connected: {self.ip_camera_url}")

    def _start_video_file(self):
        """Start video file playback."""
        if not self.video_file or not Path(self.video_file).exists():
            raise FileNotFoundError(f"Video file not found: {self.video_file}")

        self.cap = cv2.VideoCapture(self.video_file)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video file: {self.video_file}")

        logger.info(f"Video file opened: {self.video_file}")

    def _start_images(self):
        """Start image sequence playback."""
        if not self.images_folder or not Path(self.images_folder).exists():
            raise FileNotFoundError(f"Images folder not found: {self.images_folder}")

        # Get all image files
        image_exts = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
        for ext in image_exts:
            self.image_files.extend(Path(self.images_folder).glob(ext))

        if not self.image_files:
            raise RuntimeError(f"No images found in {self.images_folder}")

        self.image_files.sort()
        self.current_image_idx = 0
        logger.info(f"Found {len(self.image_files)} images")

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
            if self.source == "picamera":
                return self._capture_picamera()
            elif self.source in ["webcam", "ip_camera", "video_file"]:
                return self._capture_opencv()
            elif self.source == "images":
                return self._capture_image()
            return None

        except Exception as e:
            logger.error(f"Failed to capture frame: {e}")
            return None

    def _capture_picamera(self) -> Optional[np.ndarray]:
        """Capture from PiCamera."""
        frame = self.camera.capture_array()
        return frame

    def _capture_opencv(self) -> Optional[np.ndarray]:
        """Capture from OpenCV source (webcam/IP camera/video)."""
        ret, frame = self.cap.read()
        if not ret:
            # If video file ended, loop back
            if self.source == "video_file":
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
            
            if not ret:
                logger.warning("Failed to read frame from OpenCV source")
                return None

        # Convert BGR to RGB (OpenCV uses BGR by default)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize if needed
        if frame.shape[:2] != (self.resolution[1], self.resolution[0]):
            frame = cv2.resize(frame, self.resolution)

        return frame

    def _capture_image(self) -> Optional[np.ndarray]:
        """Capture from image sequence."""
        if self.current_image_idx >= len(self.image_files):
            self.current_image_idx = 0  # Loop back

        img_path = self.image_files[self.current_image_idx]
        frame = cv2.imread(str(img_path))
        
        if frame is None:
            logger.error(f"Could not read image: {img_path}")
            self.current_image_idx += 1
            return None

        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize if needed
        if frame.shape[:2] != (self.resolution[1], self.resolution[0]):
            frame = cv2.resize(frame, self.resolution)

        self.current_image_idx += 1
        
        # Simulate framerate
        time.sleep(1.0 / self.framerate)

        return frame

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
        if self._is_running:
            try:
                if self.source == "picamera" and self.camera:
                    self.camera.stop()
                    self.camera.close()
                elif self.cap:
                    self.cap.release()
                
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
            "source": self.source,
            "resolution": self.resolution,
            "framerate": self.framerate,
            "format": self.format,
            "is_running": self._is_running,
            "webcam_index": self.webcam_index if self.source == "webcam" else None,
            "ip_camera_url": self.ip_camera_url if self.source == "ip_camera" else None
        }

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
