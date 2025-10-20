"""Motor controller using PWM."""

import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO for development on non-RPi systems
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
        def PWM(pin, freq): return MockPWM()
        @staticmethod
        def cleanup(): pass

    class MockPWM:
        def start(self, duty): pass
        def ChangeDutyCycle(self, duty): pass
        def stop(self): pass

    GPIO = MockGPIO()

from typing import Tuple
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class MotorController:
    """DC motor controller for differential drive."""

    def __init__(
        self,
        left_pwm_pin: int = 12,
        left_dir_pin: int = 16,
        right_pwm_pin: int = 13,
        right_dir_pin: int = 18,
        pwm_frequency: int = 1000,
        max_speed: float = 1.0
    ):
        """
        Initialize motor controller.

        Args:
            left_pwm_pin: GPIO pin for left motor PWM
            left_dir_pin: GPIO pin for left motor direction
            right_pwm_pin: GPIO pin for right motor PWM
            right_dir_pin: GPIO pin for right motor direction
            pwm_frequency: PWM frequency in Hz
            max_speed: Maximum speed (0.0 to 1.0)
        """
        self.left_pwm_pin = left_pwm_pin
        self.left_dir_pin = left_dir_pin
        self.right_pwm_pin = right_pwm_pin
        self.right_dir_pin = right_dir_pin
        self.pwm_frequency = pwm_frequency
        self.max_speed = max_speed

        self.left_pwm = None
        self.right_pwm = None
        self._initialized = False

        logger.info("Motor controller initialized")

    def setup(self):
        """Setup GPIO pins and PWM."""
        try:
            GPIO.setmode(GPIO.BCM)

            # Setup direction pins
            GPIO.setup(self.left_dir_pin, GPIO.OUT)
            GPIO.setup(self.right_dir_pin, GPIO.OUT)

            # Setup PWM pins
            GPIO.setup(self.left_pwm_pin, GPIO.OUT)
            GPIO.setup(self.right_pwm_pin, GPIO.OUT)

            # Create PWM instances
            self.left_pwm = GPIO.PWM(self.left_pwm_pin, self.pwm_frequency)
            self.right_pwm = GPIO.PWM(self.right_pwm_pin, self.pwm_frequency)

            # Start PWM at 0% duty cycle
            self.left_pwm.start(0)
            self.right_pwm.start(0)

            self._initialized = True
            logger.info("Motor controller setup complete")

        except Exception as e:
            logger.error(f"Failed to setup motor controller: {e}")
            raise

    def set_motor_speeds(self, left_speed: float, right_speed: float):
        """
        Set motor speeds.

        Args:
            left_speed: Left motor speed (-1.0 to 1.0, negative = reverse)
            right_speed: Right motor speed (-1.0 to 1.0, negative = reverse)
        """
        if not self._initialized:
            logger.warning("Motor controller not initialized")
            return

        # Clamp speeds
        left_speed = max(-self.max_speed, min(self.max_speed, left_speed))
        right_speed = max(-self.max_speed, min(self.max_speed, right_speed))

        # Set left motor
        self._set_motor(
            self.left_pwm,
            self.left_dir_pin,
            left_speed
        )

        # Set right motor
        self._set_motor(
            self.right_pwm,
            self.right_dir_pin,
            right_speed
        )

        logger.debug(f"Motor speeds set: L={left_speed:.2f}, R={right_speed:.2f}")

    def _set_motor(self, pwm, dir_pin, speed: float):
        """
        Set individual motor speed and direction.

        Args:
            pwm: PWM instance
            dir_pin: Direction GPIO pin
            speed: Speed (-1.0 to 1.0)
        """
        # Determine direction
        if speed >= 0:
            GPIO.output(dir_pin, GPIO.HIGH)
            duty_cycle = abs(speed) * 100
        else:
            GPIO.output(dir_pin, GPIO.LOW)
            duty_cycle = abs(speed) * 100

        # Set PWM duty cycle
        pwm.ChangeDutyCycle(duty_cycle)

    def set_differential_drive(self, linear_speed: float, angular_speed: float, wheel_base: float = 0.4):
        """
        Set speeds using differential drive model.

        Args:
            linear_speed: Forward speed in m/s
            angular_speed: Angular velocity in rad/s
            wheel_base: Distance between wheels in meters
        """
        # Convert to wheel speeds
        # v_left = v - (omega * L / 2)
        # v_right = v + (omega * L / 2)

        left_speed = linear_speed - (angular_speed * wheel_base / 2)
        right_speed = linear_speed + (angular_speed * wheel_base / 2)

        # Normalize speeds if they exceed max speed
        max_computed = max(abs(left_speed), abs(right_speed))
        if max_computed > self.max_speed:
            scale = self.max_speed / max_computed
            left_speed *= scale
            right_speed *= scale

        self.set_motor_speeds(left_speed, right_speed)

    def stop(self):
        """Stop all motors."""
        self.set_motor_speeds(0, 0)
        logger.info("Motors stopped")

    def cleanup(self):
        """Cleanup GPIO resources."""
        self.stop()

        if self.left_pwm:
            self.left_pwm.stop()
        if self.right_pwm:
            self.right_pwm.stop()

        GPIO.cleanup()
        self._initialized = False
        logger.info("Motor controller cleaned up")

    def __enter__(self):
        """Context manager entry."""
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


class MockMotorController(MotorController):
    """Mock motor controller for development/testing without hardware."""

    def __init__(self, *args, **kwargs):
        """Initialize mock motor controller."""
        super().__init__(*args, **kwargs)
        self.current_left_speed = 0.0
        self.current_right_speed = 0.0
        logger.info("🔧 Mock Motor Controller initialized (simulated motors)")

    def setup(self):
        """Mock setup - no GPIO needed."""
        self._initialized = True
        logger.info("🔧 Mock motors setup complete")

    def set_motor_speeds(self, left_speed: float, right_speed: float):
        """Simulate motor speed setting."""
        self.current_left_speed = max(-self.max_speed, min(left_speed, self.max_speed))
        self.current_right_speed = max(-self.max_speed, min(right_speed, self.max_speed))
        
        logger.debug(f"🔧 Mock motors: L={self.current_left_speed:.2f}, R={self.current_right_speed:.2f}")

    def set_differential_drive(self, linear_velocity: float, angular_velocity: float):
        """Simulate differential drive."""
        wheel_base = 0.4  # meters
        left_speed = linear_velocity - (angular_velocity * wheel_base / 2)
        right_speed = linear_velocity + (angular_velocity * wheel_base / 2)
        
        self.set_motor_speeds(left_speed, right_speed)
        logger.debug(f"🔧 Mock differential drive: linear={linear_velocity:.2f}, angular={angular_velocity:.2f}")

    def stop(self):
        """Simulate motor stop."""
        self.current_left_speed = 0.0
        self.current_right_speed = 0.0
        logger.info("🔧 Mock motors stopped")

    def cleanup(self):
        """Mock cleanup - no GPIO to clean."""
        self._initialized = False
        logger.info("🔧 Mock motors cleaned up")
