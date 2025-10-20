"""Image preprocessing module."""

import cv2
import numpy as np
from typing import Tuple, Optional
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class ImagePreprocessor:
    """Image preprocessing for weed detection."""

    def __init__(
        self,
        target_size: Tuple[int, int] = (640, 640),
        normalize: bool = True,
        enhance: bool = True
    ):
        """
        Initialize preprocessor.

        Args:
            target_size: Target image size for model input (width, height)
            normalize: Whether to normalize pixel values to [0, 1]
            enhance: Whether to apply image enhancements
        """
        self.target_size = target_size
        self.normalize = normalize
        self.enhance = enhance

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for detection model.

        Args:
            image: Input image (BGR or RGB)

        Returns:
            Preprocessed image
        """
        if image is None or image.size == 0:
            logger.warning("Empty image received")
            return None

        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Assume OpenCV BGR format, convert to RGB
            processed = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            processed = image.copy()

        # Apply enhancements if enabled
        if self.enhance:
            processed = self._enhance_image(processed)

        # Resize to target size
        if processed.shape[:2] != self.target_size[::-1]:
            processed = cv2.resize(
                processed,
                self.target_size,
                interpolation=cv2.INTER_LINEAR
            )

        # Normalize if enabled
        if self.normalize:
            processed = processed.astype(np.float32) / 255.0

        return processed

    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply image enhancements for better detection.

        Args:
            image: Input image

        Returns:
            Enhanced image
        """
        # Convert to LAB color space for better enhancement
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        # Merge channels
        enhanced_lab = cv2.merge([l, a, b])

        # Convert back to RGB
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)

        return enhanced

    def denoise(self, image: np.ndarray, strength: int = 10) -> np.ndarray:
        """
        Apply denoising to image.

        Args:
            image: Input image
            strength: Denoising strength

        Returns:
            Denoised image
        """
        return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)

    def adjust_brightness_contrast(
        self,
        image: np.ndarray,
        brightness: int = 0,
        contrast: int = 0
    ) -> np.ndarray:
        """
        Adjust image brightness and contrast.

        Args:
            image: Input image
            brightness: Brightness adjustment (-100 to 100)
            contrast: Contrast adjustment (-100 to 100)

        Returns:
            Adjusted image
        """
        # Convert to float
        img = image.astype(np.float32)

        # Apply brightness
        if brightness != 0:
            if brightness > 0:
                shadow = brightness
                highlight = 255
            else:
                shadow = 0
                highlight = 255 + brightness
            alpha_b = (highlight - shadow) / 255
            gamma_b = shadow

            img = cv2.addWeighted(img, alpha_b, img, 0, gamma_b)

        # Apply contrast
        if contrast != 0:
            alpha_c = 131 * (contrast + 127) / (127 * (131 - contrast))
            gamma_c = 127 * (1 - alpha_c)

            img = cv2.addWeighted(img, alpha_c, img, 0, gamma_c)

        return np.clip(img, 0, 255).astype(np.uint8)

    def crop_roi(
        self,
        image: np.ndarray,
        roi: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Crop region of interest from image.

        Args:
            image: Input image
            roi: Region of interest (x, y, width, height)

        Returns:
            Cropped image
        """
        x, y, w, h = roi
        return image[y:y+h, x:x+w]

    def resize_with_padding(
        self,
        image: np.ndarray,
        target_size: Tuple[int, int],
        pad_color: Tuple[int, int, int] = (114, 114, 114)
    ) -> Tuple[np.ndarray, float, Tuple[int, int]]:
        """
        Resize image with padding to maintain aspect ratio.

        Args:
            image: Input image
            target_size: Target size (width, height)
            pad_color: Padding color (RGB)

        Returns:
            Tuple of (resized image, scale factor, (pad_x, pad_y))
        """
        h, w = image.shape[:2]
        target_w, target_h = target_size

        # Calculate scale factor
        scale = min(target_w / w, target_h / h)

        # Calculate new dimensions
        new_w = int(w * scale)
        new_h = int(h * scale)

        # Resize image
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Create padded image
        padded = np.full((target_h, target_w, 3), pad_color, dtype=np.uint8)

        # Calculate padding offsets
        pad_x = (target_w - new_w) // 2
        pad_y = (target_h - new_h) // 2

        # Place resized image in center
        padded[pad_y:pad_y+new_h, pad_x:pad_x+new_w] = resized

        return padded, scale, (pad_x, pad_y)
