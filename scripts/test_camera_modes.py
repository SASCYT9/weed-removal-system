#!/usr/bin/env python3
"""
Test camera with different sources (webcam, IP camera, etc.)
"""

import sys
import cv2
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vision.camera import Camera
from src.utils.logger import app_logger
from src.detection.yolo_detector import YOLODetector

logger = app_logger.get_logger(__name__)


def test_camera_source(source: str, **kwargs):
    """
    Test camera with specified source.
    
    Args:
        source: Camera source type
        **kwargs: Additional camera parameters
    """
    print(f"\n{'='*60}")
    print(f"Testing {source.upper()} camera")
    print(f"{'='*60}\n")
    
    try:
        # Create camera
        camera = Camera(
            resolution=(1280, 720),
            framerate=30,
            source=source,
            **kwargs
        )
        
        # Start camera
        print("Starting camera...")
        camera.start()
        print(f"✅ Camera started successfully!")
        print(f"Properties: {camera.get_properties()}\n")
        
        # Capture frames
        print("Capturing frames (press 'q' to quit, 's' to save frame)...")
        frame_count = 0
        start_time = time.time()
        
        cv2.namedWindow('Camera Test', cv2.WINDOW_NORMAL)
        
        while True:
            # Capture frame
            frame = camera.capture()
            
            if frame is None:
                print("⚠️ Failed to capture frame")
                time.sleep(0.1)
                continue
            
            frame_count += 1
            
            # Calculate FPS
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            
            # Convert RGB to BGR for OpenCV display
            display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Add info overlay
            cv2.putText(
                display_frame,
                f"Source: {source} | FPS: {fps:.1f} | Frame: {frame_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            cv2.putText(
                display_frame,
                "Press 'q' to quit, 's' to save frame",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            
            # Display frame
            cv2.imshow('Camera Test', display_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n✅ Quit requested")
                break
            elif key == ord('s'):
                filename = f"data/captures/frame_{int(time.time())}.jpg"
                Path(filename).parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(filename, display_frame)
                print(f"✅ Saved frame to {filename}")
        
        # Stop camera
        camera.stop()
        cv2.destroyAllWindows()
        
        # Print statistics
        print(f"\n{'='*60}")
        print(f"Statistics:")
        print(f"  Total frames: {frame_count}")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Average FPS: {fps:.2f}")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_detection(source: str, **kwargs):
    """Test camera with YOLO detection."""
    print(f"\n{'='*60}")
    print(f"Testing {source.upper()} camera with YOLO detection")
    print(f"{'='*60}\n")
    
    try:
        # Create camera
        camera = Camera(
            resolution=(1280, 720),
            framerate=30,
            source=source,
            **kwargs
        )
        
        # Create detector
        print("Loading YOLO model...")
        detector = YOLODetector(
            model_path="models/yolov8n.pt",  # Use .pt for better compatibility
            confidence_threshold=0.3,
            iou_threshold=0.45
        )
        detector.load_model()
        print("✅ Model loaded\n")
        
        # Start camera
        camera.start()
        
        print("Running detection (press 'q' to quit)...")
        frame_count = 0
        start_time = time.time()
        
        cv2.namedWindow('Detection Test', cv2.WINDOW_NORMAL)
        
        while True:
            # Capture frame
            frame = camera.capture()
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            frame_count += 1
            
            # Run detection
            detections = detector.detect(frame)
            
            # Calculate FPS
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            
            # Draw detections
            display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            for det in detections:
                x1, y1, x2, y2 = det.bbox
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Draw bounding box
                color = (0, 255, 0) if det.class_name == "crop" else (0, 0, 255)
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{det.class_name}: {det.confidence:.2f}"
                cv2.putText(
                    display_frame,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2
                )
            
            # Add info overlay
            cv2.putText(
                display_frame,
                f"FPS: {fps:.1f} | Detections: {len(detections)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            # Display
            cv2.imshow('Detection Test', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        camera.stop()
        cv2.destroyAllWindows()
        
        print(f"\n✅ Detection test complete (avg FPS: {fps:.2f})\n")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test camera modes')
    parser.add_argument(
        '--source',
        choices=['webcam', 'ip_camera', 'video_file', 'images'],
        default='webcam',
        help='Camera source to test'
    )
    parser.add_argument(
        '--webcam-index',
        type=int,
        default=0,
        help='Webcam index (default: 0)'
    )
    parser.add_argument(
        '--ip-camera-url',
        type=str,
        default='http://192.168.1.100:8080/video',
        help='IP camera URL'
    )
    parser.add_argument(
        '--video-file',
        type=str,
        default='data/test_video.mp4',
        help='Path to video file'
    )
    parser.add_argument(
        '--images-folder',
        type=str,
        default='data/test_images',
        help='Path to images folder'
    )
    parser.add_argument(
        '--with-detection',
        action='store_true',
        help='Test with YOLO detection'
    )
    
    args = parser.parse_args()
    
    # Prepare kwargs based on source
    kwargs = {}
    if args.source == 'webcam':
        kwargs['webcam_index'] = args.webcam_index
    elif args.source == 'ip_camera':
        kwargs['ip_camera_url'] = args.ip_camera_url
    elif args.source == 'video_file':
        kwargs['video_file'] = args.video_file
    elif args.source == 'images':
        kwargs['images_folder'] = args.images_folder
    
    # Run test
    if args.with_detection:
        success = test_detection(args.source, **kwargs)
    else:
        success = test_camera_source(args.source, **kwargs)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
