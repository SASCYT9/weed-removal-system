"""Field coverage path planning for agricultural robots.

Implements various coverage patterns for optimal field traversal.
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


@dataclass
class FieldBoundary:
    """Field boundary definition."""
    corners: List[Tuple[float, float]]  # List of (lat, lon) or (x, y) coordinates
    holes: List[List[Tuple[float, float]]] = None  # Optional obstacles/holes


class FieldCoveragePlanner:
    """Path planner for field coverage patterns."""

    def __init__(
        self,
        robot_width: float = 0.5,  # meters
        overlap: float = 0.1,  # meters
        headland_width: float = 2.0  # meters
    ):
        """
        Initialize field coverage planner.

        Args:
            robot_width: Width of robot/tool in meters
            overlap: Overlap between passes in meters
            headland_width: Width of headland (turning area) in meters
        """
        self.robot_width = robot_width
        self.overlap = overlap
        self.headland_width = headland_width
        self.spacing = robot_width - overlap

        logger.info(f"Field coverage planner initialized: "
                   f"width={robot_width}m, spacing={self.spacing}m")

    def parallel_lines(
        self,
        field: FieldBoundary,
        angle: float = 0.0,
        pattern: str = 'boustrophedon'
    ) -> List[Tuple[float, float]]:
        """
        Generate parallel line coverage pattern.

        Args:
            field: Field boundary
            angle: Orientation angle in degrees (0 = East-West)
            pattern: Coverage pattern ('boustrophedon', 'spiral', 'zigzag')

        Returns:
            List of waypoints
        """
        logger.info(f"Generating {pattern} pattern at {angle}° angle")

        # Calculate bounding box
        corners = np.array(field.corners)
        min_x, min_y = corners.min(axis=0)
        max_x, max_y = corners.max(axis=0)

        # Rotate to align with desired angle
        angle_rad = np.radians(angle)
        rotation_matrix = np.array([
            [np.cos(angle_rad), -np.sin(angle_rad)],
            [np.sin(angle_rad), np.cos(angle_rad)]
        ])

        rotated_corners = corners @ rotation_matrix.T

        # Calculate field dimensions in rotated frame
        rot_min_x, rot_min_y = rotated_corners.min(axis=0)
        rot_max_x, rot_max_y = rotated_corners.max(axis=0)

        field_width = rot_max_x - rot_min_x
        field_length = rot_max_y - rot_min_y

        # Generate parallel lines
        num_lines = int(field_width / self.spacing) + 1
        waypoints = []

        for i in range(num_lines):
            # Calculate line x position
            x = rot_min_x + self.headland_width + i * self.spacing

            if x > rot_max_x - self.headland_width:
                break

            if pattern == 'boustrophedon' or pattern == 'zigzag':
                # Alternate direction for each line
                if i % 2 == 0:
                    # Forward pass
                    y_start = rot_min_y + self.headland_width
                    y_end = rot_max_y - self.headland_width
                else:
                    # Reverse pass
                    y_start = rot_max_y - self.headland_width
                    y_end = rot_min_y + self.headland_width

                # Add waypoints for this line
                waypoints.append([x, y_start])
                waypoints.append([x, y_end])

        # Rotate waypoints back to original orientation
        waypoints = np.array(waypoints)
        inverse_rotation = rotation_matrix.T
        final_waypoints = waypoints @ inverse_rotation.T

        logger.info(f"Generated {len(final_waypoints)} waypoints")

        return [(x, y) for x, y in final_waypoints]

    def spiral_pattern(
        self,
        field: FieldBoundary,
        direction: str = 'inward'
    ) -> List[Tuple[float, float]]:
        """
        Generate spiral coverage pattern.

        Args:
            field: Field boundary
            direction: 'inward' or 'outward'

        Returns:
            List of waypoints
        """
        logger.info(f"Generating {direction} spiral pattern")

        corners = np.array(field.corners)
        min_x, min_y = corners.min(axis=0)
        max_x, max_y = corners.max(axis=0)

        waypoints = []

        if direction == 'outward':
            # Start from center, spiral outward
            current_x = (min_x + max_x) / 2
            current_y = (min_y + max_y) / 2

            offset = 0
            while True:
                # Right
                waypoints.append((current_x + offset, current_y))
                # Up
                waypoints.append((current_x + offset, current_y + offset))
                # Left
                waypoints.append((current_x - offset, current_y + offset))
                # Down
                waypoints.append((current_x - offset, current_y - offset))

                offset += self.spacing

                if (current_x + offset > max_x or current_x - offset < min_x or
                    current_y + offset > max_y or current_y - offset < min_y):
                    break

        else:
            # Start from edge, spiral inward
            current_min_x = min_x + self.headland_width
            current_max_x = max_x - self.headland_width
            current_min_y = min_y + self.headland_width
            current_max_y = max_y - self.headland_width

            while (current_max_x - current_min_x > self.spacing and
                   current_max_y - current_min_y > self.spacing):

                # Bottom edge (left to right)
                waypoints.append((current_min_x, current_min_y))
                waypoints.append((current_max_x, current_min_y))

                # Right edge (bottom to top)
                waypoints.append((current_max_x, current_max_y))

                # Top edge (right to left)
                waypoints.append((current_min_x, current_max_y))

                # Left edge (top to bottom) - but not all the way
                waypoints.append((current_min_x, current_min_y + self.spacing))

                # Shrink bounds
                current_min_x += self.spacing
                current_max_x -= self.spacing
                current_min_y += self.spacing
                current_max_y -= self.spacing

        logger.info(f"Generated {len(waypoints)} waypoints for spiral pattern")
        return waypoints

    def optimize_path(
        self,
        waypoints: List[Tuple[float, float]],
        start_position: Tuple[float, float] = None
    ) -> List[Tuple[float, float]]:
        """
        Optimize waypoint order to minimize total distance.

        Args:
            waypoints: List of waypoints
            start_position: Starting position

        Returns:
            Optimized waypoint list
        """
        if not waypoints:
            return []

        if start_position is None:
            start_position = waypoints[0]

        # Simple nearest neighbor optimization
        remaining = waypoints.copy()
        optimized = []
        current = start_position

        while remaining:
            # Find nearest waypoint
            distances = [np.linalg.norm(np.array(p) - np.array(current))
                        for p in remaining]
            nearest_idx = np.argmin(distances)

            nearest = remaining.pop(nearest_idx)
            optimized.append(nearest)
            current = nearest

        logger.info("Path optimized using nearest neighbor")
        return optimized

    def calculate_coverage_area(
        self,
        waypoints: List[Tuple[float, float]]
    ) -> float:
        """
        Calculate approximate coverage area.

        Args:
            waypoints: List of waypoints

        Returns:
            Coverage area in square meters
        """
        if len(waypoints) < 2:
            return 0.0

        # Calculate total path length
        total_length = 0.0
        for i in range(len(waypoints) - 1):
            p1 = np.array(waypoints[i])
            p2 = np.array(waypoints[i+1])
            total_length += np.linalg.norm(p2 - p1)

        # Area = length * robot_width
        coverage_area = total_length * self.robot_width

        return coverage_area

    def add_headland_turns(
        self,
        waypoints: List[Tuple[float, float]],
        turn_radius: float = 1.0
    ) -> List[Tuple[float, float]]:
        """
        Add smooth turning waypoints at headlands.

        Args:
            waypoints: Original waypoints
            turn_radius: Turning radius in meters

        Returns:
            Waypoints with smooth turns
        """
        if len(waypoints) < 3:
            return waypoints

        smooth_waypoints = [waypoints[0]]

        for i in range(1, len(waypoints) - 1):
            p1 = np.array(waypoints[i-1])
            p2 = np.array(waypoints[i])
            p3 = np.array(waypoints[i+1])

            # Check if this is a turn (angle change > threshold)
            v1 = p2 - p1
            v2 = p3 - p2

            if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                v1_norm = v1 / np.linalg.norm(v1)
                v2_norm = v2 / np.linalg.norm(v2)

                angle = np.arccos(np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0))

                if angle > np.radians(30):  # Significant turn
                    # Add arc waypoints
                    num_arc_points = max(3, int(angle / np.radians(15)))

                    for j in range(num_arc_points):
                        t = (j + 1) / (num_arc_points + 1)
                        # Simple interpolation (can be improved with Bezier curves)
                        arc_point = p2 + t * (p3 - p2) * 0.3
                        smooth_waypoints.append(tuple(arc_point))

            smooth_waypoints.append(waypoints[i])

        smooth_waypoints.append(waypoints[-1])

        logger.info(f"Added headland turns: {len(waypoints)} -> {len(smooth_waypoints)} waypoints")
        return smooth_waypoints

    def save_path(self, waypoints: List[Tuple[float, float]], filename: str):
        """
        Save waypoints to file.

        Args:
            waypoints: List of waypoints
            filename: Output filename
        """
        import json

        data = {
            'waypoints': waypoints,
            'robot_width': self.robot_width,
            'spacing': self.spacing,
            'num_points': len(waypoints)
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Path saved to {filename}")

    def load_path(self, filename: str) -> List[Tuple[float, float]]:
        """
        Load waypoints from file.

        Args:
            filename: Input filename

        Returns:
            List of waypoints
        """
        import json

        with open(filename, 'r') as f:
            data = json.load(f)

        waypoints = [tuple(wp) for wp in data['waypoints']]

        logger.info(f"Loaded {len(waypoints)} waypoints from {filename}")
        return waypoints
