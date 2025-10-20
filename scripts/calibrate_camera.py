#!/usr/bin/env python3
"""
Camera calibration utility for Raspberry Pi Camera.

This script performs camera calibration using a checkerboard pattern
to correct lens distortion and calculate camera matrix.
"""

import sys
import argparse
import numpy as np
import cv2
from pathlib import Path
import json
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vision.camera import Camera
from src.utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class CameraCalibrator:
    """Camera calibration using checkerboard pattern."""

    def __init__(
        self,
        checkerboard_size: tuple = (9, 6),
        square_size: float = 25.0  # millimeters
    ):
        """
        Initialize calibrator.

        Args:
            checkerboard_size: Number of inner corners (width, height)
            square_size: Size of checkerboard square in mm
        """
        self.checkerboard_size = checkerboard_size
        self.square_size = square_size

        # Prepare object points
        self.objp = np.zeros((checkerboard_size[0] * checkerboard_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:checkerboard_size[0], 0:checkerboard_size[1]].T.reshape(-1, 2)
        self.objp *= square_size

        # Arrays to store object points and image points
        self.objpoints = []  # 3D points in real world
        self.imgpoints = []  # 2D points in image plane

        self.camera_matrix = None
        self.dist_coeffs = None
        self.image_size = None

        logger.info(f"Calibrator initialized with {checkerboard_size} checkerboard")

    def capture_images(
        self,
        num_images: int = 20,
        output_dir: str = 'data/calibration'
    ):
        """
        Capture calibration images.

        Args:
            num_images: Number of images to capture
            output_dir: Directory to save images
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n📸 Camera Calibration - Capture Mode")
        print(f"   Target: {num_images} images")
        print(f"   Checkerboard: {self.checkerboard_size[0]}x{self.checkerboard_size[1]}")
        print(f"\n📋 Instructions:")
        print(f"   1. Print checkerboard pattern (9x6 inner corners)")
        print(f"   2. Show checkerboard to camera from different angles")
        print(f"   3. Press 's' to save image when corners detected")
        print(f"   4. Press 'q' to finish early\n")

        camera = Camera()
        camera.start()

        captured = 0
        while captured < num_images:
            # Capture frame
            frame = camera.capture()
            if frame is None:
                continue

            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

            # Find checkerboard corners
            ret, corners = cv2.findChessboardCorners(
                gray,
                self.checkerboard_size,
                None
            )

            # Draw corners if found
            display_frame = frame.copy()
            if ret:
                # Refine corners
                corners_refined = cv2.cornerSubPix(
                    gray,
                    corners,
                    (11, 11),
                    (-1, -1),
                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                )

                # Draw corners
                cv2.drawChessboardCorners(
                    display_frame,
                    self.checkerboard_size,
                    corners_refined,
                    ret
                )

                # Add text
                cv2.putText(
                    display_frame,
                    f"Checkerboard detected! Press 's' to save ({captured}/{num_images})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
            else:
                cv2.putText(
                    display_frame,
                    f"No checkerboard detected ({captured}/{num_images})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

            # Show frame
            cv2.imshow('Camera Calibration', cv2.cvtColor(display_frame, cv2.COLOR_RGB2BGR))

            # Handle key press
            key = cv2.waitKey(1) & 0xFF

            if key == ord('s') and ret:
                # Save image
                img_path = output_path / f'calibration_{captured:03d}.jpg'
                cv2.imwrite(str(img_path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

                captured += 1
                print(f"✅ Saved image {captured}/{num_images}: {img_path.name}")

                # Add to calibration data
                self.objpoints.append(self.objp)
                self.imgpoints.append(corners_refined)

                time.sleep(0.5)  # Brief pause

            elif key == ord('q'):
                print(f"\n⚠️  Early exit - captured {captured} images")
                break

        camera.stop()
        cv2.destroyAllWindows()

        print(f"\n✅ Captured {captured} calibration images")
        return captured

    def calibrate_from_images(self, image_dir: str):
        """
        Calibrate from existing images.

        Args:
            image_dir: Directory containing calibration images
        """
        image_path = Path(image_dir)
        image_files = list(image_path.glob('*.jpg')) + list(image_path.glob('*.png'))

        if not image_files:
            raise ValueError(f"No images found in {image_dir}")

        print(f"\n🔍 Processing {len(image_files)} images...")

        for img_file in image_files:
            # Read image
            img = cv2.imread(str(img_file))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            if self.image_size is None:
                self.image_size = gray.shape[::-1]

            # Find checkerboard corners
            ret, corners = cv2.findChessboardCorners(
                gray,
                self.checkerboard_size,
                None
            )

            if ret:
                # Refine corners
                corners_refined = cv2.cornerSubPix(
                    gray,
                    corners,
                    (11, 11),
                    (-1, -1),
                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                )

                self.objpoints.append(self.objp)
                self.imgpoints.append(corners_refined)

                print(f"✅ {img_file.name}")
            else:
                print(f"❌ {img_file.name} - No checkerboard found")

        print(f"\n✅ Found checkerboard in {len(self.objpoints)} images")

    def calculate_calibration(self):
        """Calculate camera calibration parameters."""
        if len(self.objpoints) < 10:
            raise ValueError(f"Need at least 10 images, got {len(self.objpoints)}")

        print(f"\n🔬 Calculating calibration parameters...")

        # Calibrate camera
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            self.objpoints,
            self.imgpoints,
            self.image_size,
            None,
            None
        )

        if not ret:
            raise RuntimeError("Camera calibration failed")

        self.camera_matrix = mtx
        self.dist_coeffs = dist

        # Calculate reprojection error
        mean_error = 0
        for i in range(len(self.objpoints)):
            imgpoints2, _ = cv2.projectPoints(
                self.objpoints[i],
                rvecs[i],
                tvecs[i],
                mtx,
                dist
            )
            error = cv2.norm(self.imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            mean_error += error

        mean_error /= len(self.objpoints)

        print(f"\n✅ Calibration completed!")
        print(f"   Reprojection error: {mean_error:.4f} pixels")
        print(f"\n📊 Camera Matrix:")
        print(f"   fx: {mtx[0,0]:.2f}")
        print(f"   fy: {mtx[1,1]:.2f}")
        print(f"   cx: {mtx[0,2]:.2f}")
        print(f"   cy: {mtx[1,2]:.2f}")
        print(f"\n📊 Distortion Coefficients:")
        print(f"   k1: {dist[0,0]:.6f}")
        print(f"   k2: {dist[0,1]:.6f}")
        print(f"   p1: {dist[0,2]:.6f}")
        print(f"   p2: {dist[0,3]:.6f}")
        print(f"   k3: {dist[0,4]:.6f}")

        return mean_error

    def save_calibration(self, output_file: str = 'config/camera_calibration.json'):
        """
        Save calibration to file.

        Args:
            output_file: Output JSON file path
        """
        if self.camera_matrix is None or self.dist_coeffs is None:
            raise ValueError("No calibration data to save")

        calibration_data = {
            'camera_matrix': self.camera_matrix.tolist(),
            'dist_coeffs': self.dist_coeffs.tolist(),
            'image_size': list(self.image_size),
            'checkerboard_size': list(self.checkerboard_size),
            'square_size': self.square_size,
            'num_images': len(self.objpoints)
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(calibration_data, f, indent=2)

        print(f"\n💾 Calibration saved to: {output_path}")

    def load_calibration(self, input_file: str = 'config/camera_calibration.json'):
        """
        Load calibration from file.

        Args:
            input_file: Input JSON file path
        """
        with open(input_file, 'r') as f:
            data = json.load(f)

        self.camera_matrix = np.array(data['camera_matrix'])
        self.dist_coeffs = np.array(data['dist_coeffs'])
        self.image_size = tuple(data['image_size'])

        print(f"\n✅ Calibration loaded from: {input_file}")

    def test_undistortion(self, test_image: str = None):
        """
        Test undistortion on an image.

        Args:
            test_image: Path to test image (if None, captures from camera)
        """
        if self.camera_matrix is None or self.dist_coeffs is None:
            raise ValueError("No calibration data available")

        if test_image:
            img = cv2.imread(test_image)
        else:
            print("\n📸 Capturing test image...")
            camera = Camera()
            camera.start()
            img = camera.capture()
            camera.stop()
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # Undistort image
        h, w = img.shape[:2]
        new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(
            self.camera_matrix,
            self.dist_coeffs,
            (w, h),
            1,
            (w, h)
        )

        undistorted = cv2.undistort(
            img,
            self.camera_matrix,
            self.dist_coeffs,
            None,
            new_camera_mtx
        )

        # Crop image
        x, y, w, h = roi
        undistorted = undistorted[y:y+h, x:x+w]

        # Show comparison
        comparison = np.hstack([
            cv2.resize(img, (640, 480)),
            cv2.resize(undistorted, (640, 480))
        ])

        cv2.imshow('Original (left) vs Undistorted (right)', comparison)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        print("\n✅ Undistortion test complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Camera calibration utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Capture calibration images
  python calibrate_camera.py capture --num-images 20

  # Calibrate from existing images
  python calibrate_camera.py calibrate --image-dir data/calibration

  # Test undistortion
  python calibrate_camera.py test

  # Full calibration workflow
  python calibrate_camera.py full
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Capture command
    capture_parser = subparsers.add_parser('capture', help='Capture calibration images')
    capture_parser.add_argument('--num-images', type=int, default=20, help='Number of images to capture')
    capture_parser.add_argument('--output-dir', default='data/calibration', help='Output directory')

    # Calibrate command
    calibrate_parser = subparsers.add_parser('calibrate', help='Calibrate from existing images')
    calibrate_parser.add_argument('--image-dir', required=True, help='Directory with calibration images')
    calibrate_parser.add_argument('--output', default='config/camera_calibration.json', help='Output file')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test undistortion')
    test_parser.add_argument('--calibration', default='config/camera_calibration.json', help='Calibration file')
    test_parser.add_argument('--image', help='Test image (if not provided, captures from camera)')

    # Full command
    full_parser = subparsers.add_parser('full', help='Full calibration workflow')
    full_parser.add_argument('--num-images', type=int, default=20, help='Number of images to capture')

    args = parser.parse_args()

    # Setup logging
    app_logger.setup(log_level='INFO')

    calibrator = CameraCalibrator()

    if args.command == 'capture':
        calibrator.capture_images(args.num_images, args.output_dir)

    elif args.command == 'calibrate':
        calibrator.calibrate_from_images(args.image_dir)
        calibrator.calculate_calibration()
        calibrator.save_calibration(args.output)

    elif args.command == 'test':
        calibrator.load_calibration(args.calibration)
        calibrator.test_undistortion(args.image if hasattr(args, 'image') else None)

    elif args.command == 'full':
        # Full workflow
        print("\n🎯 Full Camera Calibration Workflow\n")

        # Step 1: Capture
        num_captured = calibrator.capture_images(args.num_images)

        if num_captured < 10:
            print("\n❌ Not enough images for calibration")
            return

        # Step 2: Calibrate
        calibrator.calculate_calibration()

        # Step 3: Save
        calibrator.save_calibration()

        # Step 4: Test
        print("\n🧪 Testing undistortion...")
        calibrator.test_undistortion()

        print("\n🎉 Calibration complete!")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
