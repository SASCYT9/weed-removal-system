#!/usr/bin/env python3
"""
Training data collection utility.

Collect images and GPS coordinates for building a weed detection dataset.
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
import cv2
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vision.camera import Camera
from src.navigation.gps import GPS
from src.utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class DataCollector:
    """Collect training data for weed detection."""

    def __init__(
        self,
        output_dir: str = 'data/collected',
        use_gps: bool = True,
        gps_port: str = '/dev/ttyACM0'
    ):
        """
        Initialize data collector.

        Args:
            output_dir: Output directory for collected data
            use_gps: Whether to collect GPS data
            gps_port: GPS serial port
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.images_dir = self.output_dir / 'images'
        self.images_dir.mkdir(exist_ok=True)

        self.metadata_dir = self.output_dir / 'metadata'
        self.metadata_dir.mkdir(exist_ok=True)

        self.camera = Camera()
        self.gps = None

        if use_gps:
            try:
                self.gps = GPS(port=gps_port)
            except Exception as e:
                logger.warning(f"Failed to initialize GPS: {e}")
                print(f"⚠️  GPS not available, collecting images only")

        self.collection_count = 0

        logger.info(f"Data collector initialized: {output_dir}")

    def start(self):
        """Start camera and GPS."""
        self.camera.start()

        if self.gps:
            self.gps.start()
            print("✅ GPS started")

        print("✅ Camera started")

    def stop(self):
        """Stop camera and GPS."""
        self.camera.stop()

        if self.gps:
            self.gps.stop()

    def collect_single(self, label: str = None) -> dict:
        """
        Collect a single data point.

        Args:
            label: Optional label/annotation

        Returns:
            Metadata dictionary
        """
        # Capture image
        frame = self.camera.capture()
        if frame is None:
            logger.error("Failed to capture frame")
            return None

        # Get GPS data
        gps_data = None
        if self.gps:
            gps_data = self.gps.get_data()

        # Generate unique ID
        timestamp = datetime.now()
        data_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")

        # Save image
        image_filename = f"{data_id}.jpg"
        image_path = self.images_dir / image_filename

        # Convert RGB to BGR for OpenCV
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(image_path), frame_bgr)

        # Create metadata
        metadata = {
            'id': data_id,
            'timestamp': timestamp.isoformat(),
            'image_file': image_filename,
            'label': label
        }

        # Add GPS data if available
        if gps_data:
            metadata['gps'] = {
                'latitude': gps_data.latitude,
                'longitude': gps_data.longitude,
                'altitude': gps_data.altitude,
                'fix_quality': gps_data.fix_quality,
                'satellites': gps_data.satellites,
                'hdop': gps_data.hdop
            }

        # Save metadata
        metadata_path = self.metadata_dir / f"{data_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        self.collection_count += 1

        return metadata

    def collect_continuous(
        self,
        interval: float = 1.0,
        duration: float = None,
        count: int = None
    ):
        """
        Collect data continuously.

        Args:
            interval: Time between captures in seconds
            duration: Total collection duration in seconds (optional)
            count: Number of samples to collect (optional)
        """
        print(f"\n📸 Continuous Data Collection")
        print(f"   Interval: {interval}s")
        if duration:
            print(f"   Duration: {duration}s")
        if count:
            print(f"   Target: {count} samples")
        print("\n   Press Ctrl+C to stop\n")

        try:
            start_time = time.time()
            collected = 0

            while True:
                # Check termination conditions
                if duration and (time.time() - start_time) >= duration:
                    break
                if count and collected >= count:
                    break

                # Collect sample
                metadata = self.collect_single()

                if metadata:
                    collected += 1
                    elapsed = time.time() - start_time

                    # Display GPS fix quality
                    gps_status = "No GPS"
                    if metadata.get('gps'):
                        fix_quality = {
                            0: "No Fix",
                            1: "GPS",
                            2: "DGPS",
                            4: "RTK-Fixed",
                            5: "RTK-Float"
                        }.get(metadata['gps']['fix_quality'], "Unknown")
                        gps_status = f"{fix_quality} ({metadata['gps']['satellites']} sats)"

                    print(f"[{elapsed:.1f}s] Collected {collected}: "
                          f"{metadata['image_file']} | GPS: {gps_status}")

                # Wait for next interval
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n⚠️  Collection stopped by user")

        finally:
            print(f"\n✅ Collected {collected} samples")
            print(f"   Images: {self.images_dir}")
            print(f"   Metadata: {self.metadata_dir}")

    def collect_manual(self):
        """Collect data manually with keyboard control."""
        print(f"\n📸 Manual Data Collection")
        print(f"\n   Controls:")
        print(f"   - Press 's' to save image")
        print(f"   - Press 'w' to save and label as 'weed'")
        print(f"   - Press 'c' to save and label as 'crop'")
        print(f"   - Press 'q' to quit\n")

        collected = 0

        while True:
            # Capture and display frame
            frame = self.camera.capture()
            if frame is None:
                continue

            # Add info overlay
            display = frame.copy()
            cv2.putText(
                display,
                f"Collected: {collected} | Press 's' to save, 'q' to quit",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            # Show frame
            cv2.imshow('Data Collection', cv2.cvtColor(display, cv2.COLOR_RGB2BGR))

            # Handle key press
            key = cv2.waitKey(1) & 0xFF

            if key == ord('s'):
                # Save without label
                metadata = self.collect_single()
                if metadata:
                    collected += 1
                    print(f"✅ Saved: {metadata['image_file']}")

            elif key == ord('w'):
                # Save with 'weed' label
                metadata = self.collect_single(label='weed')
                if metadata:
                    collected += 1
                    print(f"✅ Saved as WEED: {metadata['image_file']}")

            elif key == ord('c'):
                # Save with 'crop' label
                metadata = self.collect_single(label='crop')
                if metadata:
                    collected += 1
                    print(f"✅ Saved as CROP: {metadata['image_file']}")

            elif key == ord('q'):
                break

        cv2.destroyAllWindows()

        print(f"\n✅ Manual collection complete")
        print(f"   Total collected: {collected}")

    def create_dataset_summary(self):
        """Create summary of collected dataset."""
        # Count images by label
        metadata_files = list(self.metadata_dir.glob('*.json'))

        labels = {}
        gps_count = 0

        for meta_file in metadata_files:
            with open(meta_file, 'r') as f:
                metadata = json.load(f)

            label = metadata.get('label', 'unlabeled')
            labels[label] = labels.get(label, 0) + 1

            if metadata.get('gps'):
                gps_count += 1

        summary = {
            'total_images': len(metadata_files),
            'labels': labels,
            'with_gps': gps_count,
            'output_dir': str(self.output_dir)
        }

        # Save summary
        summary_path = self.output_dir / 'dataset_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        # Print summary
        print(f"\n📊 Dataset Summary:")
        print(f"   Total images: {summary['total_images']}")
        print(f"   With GPS: {gps_count}")
        print(f"\n   Labels:")
        for label, count in labels.items():
            print(f"     {label}: {count}")

        return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Collect training data for weed detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Manual collection with keyboard control
  python collect_training_data.py manual

  # Continuous collection (1 image per second for 5 minutes)
  python collect_training_data.py continuous --interval 1 --duration 300

  # Collect 100 images
  python collect_training_data.py continuous --count 100

  # Without GPS
  python collect_training_data.py continuous --no-gps

  # Create dataset summary
  python collect_training_data.py summary
        """
    )

    parser.add_argument(
        'mode',
        choices=['manual', 'continuous', 'summary'],
        help='Collection mode'
    )
    parser.add_argument('--output-dir', default='data/collected', help='Output directory')
    parser.add_argument('--no-gps', action='store_true', help='Disable GPS')
    parser.add_argument('--gps-port', default='/dev/ttyACM0', help='GPS serial port')
    parser.add_argument('--interval', type=float, default=1.0, help='Capture interval (seconds)')
    parser.add_argument('--duration', type=float, help='Collection duration (seconds)')
    parser.add_argument('--count', type=int, help='Number of samples to collect')

    args = parser.parse_args()

    # Setup logging
    app_logger.setup(log_level='INFO')

    collector = DataCollector(
        output_dir=args.output_dir,
        use_gps=not args.no_gps,
        gps_port=args.gps_port
    )

    if args.mode == 'summary':
        collector.create_dataset_summary()
        return

    try:
        collector.start()

        if args.mode == 'manual':
            collector.collect_manual()
        elif args.mode == 'continuous':
            collector.collect_continuous(
                interval=args.interval,
                duration=args.duration,
                count=args.count
            )

    finally:
        collector.stop()
        collector.create_dataset_summary()


if __name__ == '__main__':
    main()
