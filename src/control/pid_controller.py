"""PID Controller implementation."""

import time
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class PIDController:
    """Proportional-Integral-Derivative controller."""

    def __init__(
        self,
        kp: float = 1.0,
        ki: float = 0.1,
        kd: float = 0.05,
        output_limits: tuple = (-1.0, 1.0),
        integral_limits: tuple = (-10.0, 10.0)
    ):
        """
        Initialize PID controller.

        Args:
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
            output_limits: Tuple of (min, max) output values
            integral_limits: Tuple of (min, max) integral values (anti-windup)
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limits = output_limits
        self.integral_limits = integral_limits

        self._integral = 0.0
        self._previous_error = 0.0
        self._previous_time = None

        logger.info(f"PID Controller initialized: Kp={kp}, Ki={ki}, Kd={kd}")

    def compute(self, setpoint: float, measured_value: float, dt: float = None) -> float:
        """
        Compute PID output.

        Args:
            setpoint: Target value
            measured_value: Current measured value
            dt: Time step in seconds (if None, will compute from system time)

        Returns:
            Control output
        """
        # Calculate error
        error = setpoint - measured_value

        # Calculate time step
        current_time = time.time()
        if dt is None:
            if self._previous_time is not None:
                dt = current_time - self._previous_time
            else:
                dt = 0.0

        if dt <= 0:
            dt = 0.01  # Minimum time step

        self._previous_time = current_time

        # Proportional term
        p_term = self.kp * error

        # Integral term with anti-windup
        self._integral += error * dt
        self._integral = max(
            self.integral_limits[0],
            min(self.integral_limits[1], self._integral)
        )
        i_term = self.ki * self._integral

        # Derivative term
        if dt > 0:
            derivative = (error - self._previous_error) / dt
        else:
            derivative = 0.0
        d_term = self.kd * derivative

        # Calculate output
        output = p_term + i_term + d_term

        # Apply output limits
        output = max(
            self.output_limits[0],
            min(self.output_limits[1], output)
        )

        # Store previous error
        self._previous_error = error

        logger.debug(
            f"PID: error={error:.3f}, P={p_term:.3f}, I={i_term:.3f}, "
            f"D={d_term:.3f}, output={output:.3f}"
        )

        return output

    def reset(self):
        """Reset PID controller state."""
        self._integral = 0.0
        self._previous_error = 0.0
        self._previous_time = None
        logger.info("PID Controller reset")

    def set_gains(self, kp: float = None, ki: float = None, kd: float = None):
        """
        Update PID gains.

        Args:
            kp: Proportional gain (optional)
            ki: Integral gain (optional)
            kd: Derivative gain (optional)
        """
        if kp is not None:
            self.kp = kp
        if ki is not None:
            self.ki = ki
        if kd is not None:
            self.kd = kd

        logger.info(f"PID gains updated: Kp={self.kp}, Ki={self.ki}, Kd={self.kd}")

    def get_state(self) -> dict:
        """
        Get current PID state.

        Returns:
            Dictionary with PID state
        """
        return {
            'kp': self.kp,
            'ki': self.ki,
            'kd': self.kd,
            'integral': self._integral,
            'previous_error': self._previous_error
        }
