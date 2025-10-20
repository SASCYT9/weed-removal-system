#!/usr/bin/env python3
"""
Weed Removal Robot - Main Application
Autonomous robot for precision weed removal using computer vision
"""

import time
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config_loader import config
from src.utils.logger import app_logger
from src.vision.camera import Camera
from src.vision.preprocessor import ImagePreprocessor
from src.detection.yolo_detector import YOLODetector
from src.navigation.gps import GPS
from src.navigation.kalman_filter import NavigationKalmanFilter
from src.control.motor_controller import MotorController
from src.control.pure_pursuit import PurePursuit
from src.control.pid_controller import PIDController
from src.weeding.weeder import Weeder
from src.telemetry.mqtt_client import MQTTClient
from src.telemetry.web_server import WebServer

# Setup logger
logger = app_logger.get_logger(__name__)


class WeedRemovalRobot:
    """Main robot controller integrating all subsystems."""

    def __init__(self, config_path: str = None):
        """
        Initialize robot.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = config
        if config_path:
            self.config.config_path = Path(config_path)
        self.config.load()

        # Setup logging
        log_config = self.config.get('telemetry.logging', {})
        app_logger.setup(
            log_level=log_config.get('level', 'INFO'),
            log_file=log_config.get('log_file'),
            max_bytes=log_config.get('max_bytes', 10485760),
            backup_count=log_config.get('backup_count', 5)
        )

        logger.info("=" * 60)
        logger.info("Initializing Weed Removal Robot System")
        logger.info("=" * 60)

        # Initialize subsystems
        self._init_vision()
        self._init_detection()
        self._init_navigation()
        self._init_control()
        self._init_weeding()
        self._init_telemetry()

        # Robot state
        self.running = False
        self.paused = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Robot initialization complete")

    def _init_vision(self):
        """Initialize vision subsystem."""
        logger.info("Initializing vision subsystem...")

        cam_config = self.config.get('camera', {})
        self.camera = Camera(
            resolution=tuple(cam_config.get('resolution', [1920, 1080])),
            framerate=cam_config.get('framerate', 30),
            format=cam_config.get('format', 'RGB888')
        )

        det_config = self.config.get('detection', {})
        self.preprocessor = ImagePreprocessor(
            target_size=tuple(det_config.get('input_size', [640, 640])),
            normalize=True,
            enhance=True
        )

        logger.info("Vision subsystem initialized")

    def _init_detection(self):
        """Initialize detection subsystem."""
        logger.info("Initializing detection subsystem...")

        det_config = self.config.get('detection', {})
        self.detector = YOLODetector(
            model_path=det_config.get('model_path', 'models/yolov8n.tflite'),
            confidence_threshold=det_config.get('confidence_threshold', 0.5),
            iou_threshold=det_config.get('iou_threshold', 0.45),
            input_size=tuple(det_config.get('input_size', [640, 640])),
            class_names=det_config.get('classes', ['weed', 'crop'])
        )

        logger.info("Detection subsystem initialized")

    def _init_navigation(self):
        """Initialize navigation subsystem."""
        logger.info("Initializing navigation subsystem...")

        gps_config = self.config.get('navigation.gps', {})
        self.gps = GPS(
            port=gps_config.get('port', '/dev/ttyACM0'),
            baudrate=gps_config.get('baudrate', 38400),
            timeout=gps_config.get('timeout', 1.0)
        )

        kf_config = self.config.get('navigation.kalman_filter', {})
        self.kalman_filter = NavigationKalmanFilter(
            process_noise=kf_config.get('process_noise', 0.1),
            measurement_noise=kf_config.get('measurement_noise', 0.1),
            initial_estimate_error=kf_config.get('initial_estimate_error', 1.0)
        )

        logger.info("Navigation subsystem initialized")

    def _init_control(self):
        """Initialize control subsystem."""
        logger.info("Initializing control subsystem...")

        motor_config = self.config.get('control.motors', {})
        self.motor_controller = MotorController(
            left_pwm_pin=motor_config.get('left_pwm_pin', 12),
            left_dir_pin=motor_config.get('left_dir_pin', 16),
            right_pwm_pin=motor_config.get('right_pwm_pin', 13),
            right_dir_pin=motor_config.get('right_dir_pin', 18),
            max_speed=self.config.get('control.pure_pursuit.max_speed', 1.0)
        )

        pid_config = self.config.get('control.pid', {})
        self.pid_controller = PIDController(
            kp=pid_config.get('kp', 1.0),
            ki=pid_config.get('ki', 0.1),
            kd=pid_config.get('kd', 0.05)
        )

        pp_config = self.config.get('control.pure_pursuit', {})
        self.pure_pursuit = PurePursuit(
            lookahead_distance=pp_config.get('lookahead_distance', 1.0),
            wheel_base=pp_config.get('wheel_base', 0.4),
            max_speed=pp_config.get('max_speed', 0.5)
        )

        logger.info("Control subsystem initialized")

    def _init_weeding(self):
        """Initialize weeding subsystem."""
        logger.info("Initializing weeding subsystem...")

        weed_config = self.config.get('weeding', {})
        self.weeder = Weeder(
            mechanism_pin=weed_config.get('mechanism_pin', 22),
            activation_duration=weed_config.get('activation_duration', 0.5),
            offset_x=weed_config.get('offset_x', 0.0),
            offset_y=weed_config.get('offset_y', 0.2)
        )

        logger.info("Weeding subsystem initialized")

    def _init_telemetry(self):
        """Initialize telemetry subsystem."""
        logger.info("Initializing telemetry subsystem...")

        # MQTT
        mqtt_config = self.config.get('telemetry.mqtt', {})
        self.mqtt_client = MQTTClient(
            broker=mqtt_config.get('broker', 'localhost'),
            port=mqtt_config.get('port', 1883),
            topic_prefix=mqtt_config.get('topic_prefix', 'weed_robot'),
            keepalive=mqtt_config.get('keepalive', 60)
        )

        # Web Server
        web_config = self.config.get('telemetry.web', {})
        self.web_server = WebServer(
            host=web_config.get('host', '0.0.0.0'),
            port=web_config.get('port', 5000),
            debug=web_config.get('debug', False)
        )

        logger.info("Telemetry subsystem initialized")

    def start(self):
        """Start robot operation."""
        logger.info("Starting robot operation...")

        try:
            # Start subsystems
            self.camera.start()
            self.detector.load_model()
            self.gps.start()
            self.motor_controller.setup()
            self.weeder.setup()
            self.mqtt_client.connect()
            self.web_server.run_in_background()

            self.running = True
            self.web_server.update_state('status', 'running')

            logger.info("All subsystems started successfully")

            # Main control loop
            self._main_loop()

        except Exception as e:
            logger.error(f"Error starting robot: {e}")
            self.stop()

    def _main_loop(self):
        """Main control loop."""
        logger.info("Entering main control loop")

        update_rate = self.config.get('system.update_rate', 20)
        dt = 1.0 / update_rate

        while self.running:
            try:
                loop_start = time.time()

                if not self.paused:
                    # 1. Capture image
                    frame = self.camera.capture()
                    if frame is None:
                        continue

                    # 2. Preprocess image
                    processed_frame = self.preprocessor.preprocess(frame)

                    # 3. Detect weeds
                    detections = self.detector.detect(processed_frame)
                    weeds = self.detector.get_weed_detections(detections)

                    # 4. Get GPS data
                    gps_data = self.gps.get_data()

                    # 5. Update Kalman filter
                    if gps_data and gps_data.latitude:
                        self.kalman_filter.update(
                            position=(gps_data.latitude, gps_data.longitude),
                            velocity=(gps_data.speed * 0.514444, 0),  # Convert knots to m/s
                            heading=gps_data.heading
                        )
                    self.kalman_filter.predict(dt)

                    # 6. Get current state
                    state = self.kalman_filter.get_state()

                    # 7. Path following (if path is set)
                    if len(self.pure_pursuit.path) > 0:
                        linear_vel, angular_vel = self.pure_pursuit.compute(
                            (state['x'], state['y']),
                            state['heading']
                        )
                        self.motor_controller.set_differential_drive(
                            linear_vel,
                            angular_vel
                        )

                    # 8. Process weeds
                    if len(weeds) > 0:
                        self.weeder.process_detections(
                            weeds,
                            robot_position=(state['x'], state['y'])
                        )

                    # 9. Publish telemetry
                    self._publish_telemetry(state, gps_data, detections)

                # Sleep to maintain update rate
                elapsed = time.time() - loop_start
                if elapsed < dt:
                    time.sleep(dt - elapsed)

            except Exception as e:
                logger.error(f"Error in main loop: {e}")

        logger.info("Main control loop ended")

    def _publish_telemetry(self, state, gps_data, detections):
        """Publish telemetry data."""
        # MQTT
        if state:
            self.mqtt_client.publish_telemetry({
                'x': state['x'],
                'y': state['y'],
                'heading': state['heading'],
                'speed': state['speed']
            })

        if gps_data:
            self.mqtt_client.publish_gps({
                'latitude': gps_data.latitude,
                'longitude': gps_data.longitude,
                'altitude': gps_data.altitude,
                'fix_quality': gps_data.fix_quality
            })

        if detections:
            detection_list = [
                {
                    'class_name': d.class_name,
                    'confidence': d.confidence,
                    'bbox': d.bbox,
                    'center': d.center
                }
                for d in detections
            ]
            self.mqtt_client.publish_detection(detection_list)

        # Web Server
        if state:
            self.web_server.update_position(
                state['x'],
                state['y'],
                state['heading']
            )

        if gps_data:
            self.web_server.update_gps({
                'latitude': gps_data.latitude,
                'longitude': gps_data.longitude,
                'fix_quality': gps_data.fix_quality
            })

        if detections:
            self.web_server.update_detections(detection_list)

    def stop(self):
        """Stop robot operation."""
        logger.info("Stopping robot...")

        self.running = False

        # Stop all subsystems
        try:
            self.motor_controller.stop()
            self.motor_controller.cleanup()
        except Exception as e:
            logger.error(f"Error stopping motors: {e}")

        try:
            self.camera.stop()
        except Exception as e:
            logger.error(f"Error stopping camera: {e}")

        try:
            self.gps.stop()
        except Exception as e:
            logger.error(f"Error stopping GPS: {e}")

        try:
            self.weeder.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up weeder: {e}")

        try:
            self.mqtt_client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting MQTT: {e}")

        self.web_server.update_state('status', 'stopped')

        logger.info("Robot stopped")

    def pause(self):
        """Pause robot operation."""
        self.paused = True
        self.motor_controller.stop()
        self.web_server.update_state('status', 'paused')
        logger.info("Robot paused")

    def resume(self):
        """Resume robot operation."""
        self.paused = False
        self.web_server.update_state('status', 'running')
        logger.info("Robot resumed")

    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Weed Removal Robot')
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    args = parser.parse_args()

    # Create and start robot
    robot = WeedRemovalRobot(config_path=args.config)

    try:
        robot.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        robot.stop()


if __name__ == '__main__':
    main()
