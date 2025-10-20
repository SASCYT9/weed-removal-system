"""Tests for control module."""

import pytest
import numpy as np
from src.control.pid_controller import PIDController
from src.control.pure_pursuit import PurePursuit


class TestPIDController:
    """Test PIDController class."""

    def test_init(self):
        """Test PID initialization."""
        pid = PIDController(kp=1.0, ki=0.1, kd=0.05)

        assert pid.kp == 1.0
        assert pid.ki == 0.1
        assert pid.kd == 0.05

    def test_compute(self):
        """Test PID computation."""
        pid = PIDController(kp=1.0, ki=0.0, kd=0.0)

        # Test proportional only
        output = pid.compute(setpoint=10.0, measured_value=5.0, dt=0.1)

        # With only P term, output should be kp * error = 1.0 * 5.0 = 5.0
        # But clamped to output_limits
        assert -1.0 <= output <= 1.0

    def test_reset(self):
        """Test PID reset."""
        pid = PIDController(kp=1.0, ki=0.1, kd=0.05)

        # Compute some values
        pid.compute(10.0, 5.0, 0.1)
        pid.compute(10.0, 6.0, 0.1)

        # Reset
        pid.reset()

        assert pid._integral == 0.0
        assert pid._previous_error == 0.0

    def test_set_gains(self):
        """Test updating PID gains."""
        pid = PIDController(kp=1.0, ki=0.1, kd=0.05)

        pid.set_gains(kp=2.0, ki=0.2)

        assert pid.kp == 2.0
        assert pid.ki == 0.2
        assert pid.kd == 0.05  # Unchanged


class TestPurePursuit:
    """Test PurePursuit class."""

    def test_init(self):
        """Test Pure Pursuit initialization."""
        pp = PurePursuit(
            lookahead_distance=1.0,
            wheel_base=0.4,
            max_speed=0.5
        )

        assert pp.lookahead_distance == 1.0
        assert pp.wheel_base == 0.4
        assert pp.max_speed == 0.5

    def test_set_path(self):
        """Test setting path."""
        pp = PurePursuit()

        path = [(0, 0), (1, 0), (2, 0), (3, 0)]
        pp.set_path(path)

        assert len(pp.path) == 4
        assert pp.current_index == 0

    def test_compute(self):
        """Test control computation."""
        pp = PurePursuit(lookahead_distance=1.0)

        # Set simple straight path
        path = [(0, 0), (1, 0), (2, 0), (3, 0)]
        pp.set_path(path)

        # Compute control from origin
        linear_vel, angular_vel = pp.compute(
            current_position=(0, 0),
            current_heading=0.0
        )

        assert isinstance(linear_vel, float)
        assert isinstance(angular_vel, float)

    def test_is_goal_reached(self):
        """Test goal reached check."""
        pp = PurePursuit()

        path = [(0, 0), (1, 0), (2, 0)]
        pp.set_path(path)

        # Not at goal
        assert not pp.is_goal_reached((0, 0), goal_threshold=0.1)

        # At goal
        assert pp.is_goal_reached((2, 0), goal_threshold=0.1)

    def test_get_progress(self):
        """Test progress calculation."""
        pp = PurePursuit()

        path = [(0, 0), (1, 0), (2, 0), (3, 0)]
        pp.set_path(path)

        # At start
        assert pp.get_progress() == 0.0

        # Move index
        pp.current_index = 2
        assert pp.get_progress() == 50.0


if __name__ == "__main__":
    pytest.main([__file__])
