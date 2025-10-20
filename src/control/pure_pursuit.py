"""Pure Pursuit path following algorithm."""

import numpy as np
from typing import List, Tuple, Optional
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class PurePursuit:
    """Pure Pursuit path following controller."""

    def __init__(
        self,
        lookahead_distance: float = 1.0,
        wheel_base: float = 0.4,
        max_speed: float = 0.5,
        min_lookahead: float = 0.3,
        max_lookahead: float = 2.0
    ):
        """
        Initialize Pure Pursuit controller.

        Args:
            lookahead_distance: Lookahead distance in meters
            wheel_base: Wheelbase of robot in meters
            max_speed: Maximum linear speed in m/s
            min_lookahead: Minimum lookahead distance
            max_lookahead: Maximum lookahead distance
        """
        self.lookahead_distance = lookahead_distance
        self.wheel_base = wheel_base
        self.max_speed = max_speed
        self.min_lookahead = min_lookahead
        self.max_lookahead = max_lookahead

        self.path = []
        self.current_index = 0

        logger.info(
            f"Pure Pursuit initialized: lookahead={lookahead_distance}m, "
            f"wheelbase={wheel_base}m, max_speed={max_speed}m/s"
        )

    def set_path(self, path: List[Tuple[float, float]]):
        """
        Set path to follow.

        Args:
            path: List of (x, y) waypoints
        """
        self.path = path
        self.current_index = 0
        logger.info(f"Path set with {len(path)} waypoints")

    def compute(
        self,
        current_position: Tuple[float, float],
        current_heading: float
    ) -> Tuple[float, float]:
        """
        Compute control commands.

        Args:
            current_position: Current (x, y) position
            current_heading: Current heading in radians

        Returns:
            Tuple of (linear_velocity, angular_velocity)
        """
        if len(self.path) == 0:
            logger.warning("No path set")
            return (0.0, 0.0)

        # Find lookahead point
        lookahead_point = self._find_lookahead_point(current_position)

        if lookahead_point is None:
            logger.debug("No lookahead point found, path may be complete")
            return (0.0, 0.0)

        # Calculate control commands
        linear_vel, angular_vel = self._calculate_control(
            current_position,
            current_heading,
            lookahead_point
        )

        return (linear_vel, angular_vel)

    def _find_lookahead_point(
        self,
        current_position: Tuple[float, float]
    ) -> Optional[Tuple[float, float]]:
        """
        Find lookahead point on path.

        Args:
            current_position: Current (x, y) position

        Returns:
            Lookahead point (x, y) or None if not found
        """
        cx, cy = current_position

        # Adaptive lookahead distance based on speed
        # (could be enhanced with actual speed feedback)
        ld = self.lookahead_distance

        # Search for lookahead point starting from current index
        for i in range(self.current_index, len(self.path)):
            px, py = self.path[i]
            distance = np.sqrt((px - cx)**2 + (py - cy)**2)

            # Update current index to closest point
            if i == self.current_index and distance < ld * 0.5:
                self.current_index = min(i + 1, len(self.path) - 1)

            # Find point at lookahead distance
            if distance >= ld:
                return (px, py)

        # If no point found at lookahead distance, return last point
        if len(self.path) > 0:
            return self.path[-1]

        return None

    def _calculate_control(
        self,
        current_position: Tuple[float, float],
        current_heading: float,
        lookahead_point: Tuple[float, float]
    ) -> Tuple[float, float]:
        """
        Calculate control commands using Pure Pursuit algorithm.

        Args:
            current_position: Current (x, y) position
            current_heading: Current heading in radians
            lookahead_point: Lookahead point (x, y)

        Returns:
            Tuple of (linear_velocity, angular_velocity)
        """
        cx, cy = current_position
        gx, gy = lookahead_point

        # Transform lookahead point to robot frame
        dx = gx - cx
        dy = gy - cy

        # Rotate to robot frame
        alpha = np.arctan2(dy, dx) - current_heading

        # Normalize angle to [-pi, pi]
        alpha = np.arctan2(np.sin(alpha), np.cos(alpha))

        # Calculate distance to lookahead point
        ld = np.sqrt(dx**2 + dy**2)

        # Pure Pursuit curvature calculation
        # curvature = 2 * sin(alpha) / ld
        if ld > 0.01:
            curvature = 2.0 * np.sin(alpha) / ld
        else:
            curvature = 0.0

        # Calculate target angular velocity
        # omega = v * curvature
        linear_vel = self.max_speed
        angular_vel = linear_vel * curvature

        # Limit angular velocity
        max_angular_vel = 2.0  # rad/s
        angular_vel = np.clip(angular_vel, -max_angular_vel, max_angular_vel)

        # Reduce linear velocity for sharp turns
        turn_factor = 1.0 - min(abs(angular_vel) / max_angular_vel, 1.0) * 0.5
        linear_vel *= turn_factor

        logger.debug(
            f"Pure Pursuit: ld={ld:.2f}, alpha={np.degrees(alpha):.1f}°, "
            f"v={linear_vel:.2f}, omega={angular_vel:.2f}"
        )

        return (linear_vel, angular_vel)

    def is_goal_reached(
        self,
        current_position: Tuple[float, float],
        goal_threshold: float = 0.2
    ) -> bool:
        """
        Check if goal is reached.

        Args:
            current_position: Current (x, y) position
            goal_threshold: Distance threshold in meters

        Returns:
            True if goal reached
        """
        if len(self.path) == 0:
            return True

        goal = self.path[-1]
        distance = np.sqrt(
            (goal[0] - current_position[0])**2 +
            (goal[1] - current_position[1])**2
        )

        return distance < goal_threshold

    def get_progress(self) -> float:
        """
        Get path following progress.

        Returns:
            Progress as percentage (0-100)
        """
        if len(self.path) == 0:
            return 100.0

        return (self.current_index / len(self.path)) * 100.0

    def reset(self):
        """Reset controller state."""
        self.current_index = 0
        logger.info("Pure Pursuit controller reset")
