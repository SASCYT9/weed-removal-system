"""Extended Kalman Filter for GPS/IMU fusion."""

import numpy as np
from filterpy.kalman import ExtendedKalmanFilter
from typing import Tuple, Optional
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class NavigationKalmanFilter:
    """Extended Kalman Filter for fusing GPS and IMU data."""

    def __init__(
        self,
        process_noise: float = 0.1,
        measurement_noise: float = 0.1,
        initial_estimate_error: float = 1.0
    ):
        """
        Initialize Kalman Filter.

        State vector: [x, y, vx, vy, heading, heading_rate]
        - x, y: position in meters
        - vx, vy: velocity in m/s
        - heading: orientation in radians
        - heading_rate: angular velocity in rad/s

        Args:
            process_noise: Process noise covariance
            measurement_noise: Measurement noise covariance
            initial_estimate_error: Initial estimate error covariance
        """
        self.dim_x = 6  # State dimension
        self.dim_z = 5  # Measurement dimension (x, y, vx, vy, heading)

        # Create Extended Kalman Filter
        self.ekf = ExtendedKalmanFilter(dim_x=self.dim_x, dim_z=self.dim_z)

        # Initial state
        self.ekf.x = np.zeros(self.dim_x)

        # State covariance matrix
        self.ekf.P = np.eye(self.dim_x) * initial_estimate_error

        # Process noise covariance
        self.ekf.Q = np.eye(self.dim_x) * process_noise

        # Measurement noise covariance
        self.ekf.R = np.eye(self.dim_z) * measurement_noise

        self.dt = 0.05  # Time step (20 Hz)
        self._initialized = False

        logger.info("Kalman Filter initialized")

    def predict(self, dt: Optional[float] = None):
        """
        Predict next state.

        Args:
            dt: Time step in seconds (optional)
        """
        if dt is not None:
            self.dt = dt

        # State transition function
        def state_transition(x, dt):
            """Non-linear state transition."""
            x_new = np.copy(x)

            # Update position based on velocity
            x_new[0] += x[2] * dt  # x += vx * dt
            x_new[1] += x[3] * dt  # y += vy * dt

            # Update heading based on heading rate
            x_new[4] += x[5] * dt  # heading += heading_rate * dt

            # Normalize heading to [-pi, pi]
            x_new[4] = self._normalize_angle(x_new[4])

            return x_new

        # Jacobian of state transition
        def jacobian_f(x, dt):
            """Jacobian of state transition function."""
            F = np.eye(self.dim_x)
            F[0, 2] = dt  # dx/dvx
            F[1, 3] = dt  # dy/dvy
            F[4, 5] = dt  # dheading/dheading_rate
            return F

        # Perform prediction
        self.ekf.x = state_transition(self.ekf.x, self.dt)
        F = jacobian_f(self.ekf.x, self.dt)
        self.ekf.P = F @ self.ekf.P @ F.T + self.ekf.Q

    def update(
        self,
        position: Optional[Tuple[float, float]] = None,
        velocity: Optional[Tuple[float, float]] = None,
        heading: Optional[float] = None
    ):
        """
        Update filter with measurements.

        Args:
            position: (x, y) position in meters
            velocity: (vx, vy) velocity in m/s
            heading: Heading in radians
        """
        if not self._initialized and position is not None:
            # Initialize state with first measurement
            self.ekf.x[0] = position[0]
            self.ekf.x[1] = position[1]
            if velocity is not None:
                self.ekf.x[2] = velocity[0]
                self.ekf.x[3] = velocity[1]
            if heading is not None:
                self.ekf.x[4] = self._normalize_angle(heading)
            self._initialized = True
            logger.info("Kalman Filter initialized with first measurement")
            return

        # Build measurement vector
        z = np.zeros(self.dim_z)
        H = np.zeros((self.dim_z, self.dim_x))

        idx = 0
        if position is not None:
            z[idx:idx+2] = position
            H[idx:idx+2, 0:2] = np.eye(2)
            idx += 2

        if velocity is not None:
            z[idx:idx+2] = velocity
            H[idx:idx+2, 2:4] = np.eye(2)
            idx += 2

        if heading is not None:
            z[idx] = self._normalize_angle(heading)
            H[idx, 4] = 1.0
            idx += 1

        # Measurement function
        def measurement_function(x):
            """Convert state to measurement space."""
            return H @ x

        # Perform update
        if idx > 0:
            z_pred = measurement_function(self.ekf.x)
            y = z[:idx] - z_pred[:idx]  # Innovation

            # Normalize angle innovation
            if heading is not None:
                y[idx-1] = self._normalize_angle(y[idx-1])

            S = H[:idx] @ self.ekf.P @ H[:idx].T + self.ekf.R[:idx, :idx]
            K = self.ekf.P @ H[:idx].T @ np.linalg.inv(S)

            self.ekf.x = self.ekf.x + K @ y
            self.ekf.P = (np.eye(self.dim_x) - K @ H[:idx]) @ self.ekf.P

            # Normalize heading
            self.ekf.x[4] = self._normalize_angle(self.ekf.x[4])

    def get_state(self) -> dict:
        """
        Get current state estimate.

        Returns:
            Dictionary with state variables
        """
        return {
            'x': self.ekf.x[0],
            'y': self.ekf.x[1],
            'vx': self.ekf.x[2],
            'vy': self.ekf.x[3],
            'heading': self.ekf.x[4],
            'heading_rate': self.ekf.x[5],
            'speed': np.sqrt(self.ekf.x[2]**2 + self.ekf.x[3]**2)
        }

    def get_position(self) -> Tuple[float, float]:
        """Get estimated position."""
        return (self.ekf.x[0], self.ekf.x[1])

    def get_velocity(self) -> Tuple[float, float]:
        """Get estimated velocity."""
        return (self.ekf.x[2], self.ekf.x[3])

    def get_heading(self) -> float:
        """Get estimated heading."""
        return self.ekf.x[4]

    def get_covariance(self) -> np.ndarray:
        """Get state covariance matrix."""
        return self.ekf.P

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """
        Normalize angle to [-pi, pi].

        Args:
            angle: Angle in radians

        Returns:
            Normalized angle
        """
        while angle > np.pi:
            angle -= 2 * np.pi
        while angle < -np.pi:
            angle += 2 * np.pi
        return angle

    def is_initialized(self) -> bool:
        """Check if filter is initialized."""
        return self._initialized

    def reset(self):
        """Reset filter to initial state."""
        self.ekf.x = np.zeros(self.dim_x)
        self.ekf.P = np.eye(self.dim_x)
        self._initialized = False
        logger.info("Kalman Filter reset")
