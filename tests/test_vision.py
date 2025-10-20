"""Tests for vision module."""

import pytest
import numpy as np
from src.vision.preprocessor import ImagePreprocessor


class TestImagePreprocessor:
    """Test ImagePreprocessor class."""

    def test_init(self):
        """Test preprocessor initialization."""
        preprocessor = ImagePreprocessor(
            target_size=(640, 640),
            normalize=True,
            enhance=True
        )

        assert preprocessor.target_size == (640, 640)
        assert preprocessor.normalize is True
        assert preprocessor.enhance is True

    def test_preprocess(self):
        """Test image preprocessing."""
        preprocessor = ImagePreprocessor(target_size=(640, 640))

        # Create dummy image
        image = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

        # Preprocess
        processed = preprocessor.preprocess(image)

        # Check shape
        assert processed.shape == (640, 640, 3)

    def test_resize_with_padding(self):
        """Test resize with padding."""
        preprocessor = ImagePreprocessor()

        # Create dummy image
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # Resize
        resized, scale, (pad_x, pad_y) = preprocessor.resize_with_padding(
            image,
            (640, 640)
        )

        # Check output
        assert resized.shape == (640, 640, 3)
        assert isinstance(scale, float)
        assert isinstance(pad_x, int)
        assert isinstance(pad_y, int)

    def test_adjust_brightness_contrast(self):
        """Test brightness/contrast adjustment."""
        preprocessor = ImagePreprocessor()

        # Create dummy image
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # Adjust
        adjusted = preprocessor.adjust_brightness_contrast(
            image,
            brightness=20,
            contrast=10
        )

        # Check output
        assert adjusted.shape == image.shape
        assert adjusted.dtype == np.uint8


if __name__ == "__main__":
    pytest.main([__file__])
