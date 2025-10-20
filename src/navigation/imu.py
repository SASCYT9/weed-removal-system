"""IMU (Inertial Measurement Unit) module for attitude and acceleration measurement."""

import serial
import time
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from threading import Thread, Lock
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


@dataclass
class IMUData:
    """IMU data container."""
    accel_x: float  # m/s²
    accel_y: float
    accel_z: float
    gyro_x: float  # rad/s
    gyro_y: float
    gyro_z: float
    mag_x: float  # μT (magnetometer, if available)
    mag_y: float
    mag_z: float
    temperature: float  # °C
    timestamp: float


class IMU:
    """IMU interface for MPU6050, MPU9250, or similar sensors."""

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 115200,
        timeout: float = 1.0
    ):
        """
        Initialize IMU.

        Args:
            port: Serial port for IMU
            baudrate: Serial baudrate
            timeout: Serial timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.serial = None
        self._running = False
        self._thread = None
        self._lock = Lock()
        self._current_data = None

        # Calibration offsets
        self.accel_offset = np.zeros(3)
        self.gyro_offset = np.zeros(3)
        self.mag_offset = np.zeros(3)

        logger.info(f"Initializing IMU on {port} at {baudrate} baud")

    def start(self):
        """Start IMU reading thread."""
        try:
            self.serial = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout
            )

            self._running = True
            self._thread = Thread(target=self._read_loop, daemon=True)
            self._thread.start()

            logger.info("IMU started successfully")

        except Exception as e:
            logger.error(f"Failed to start IMU: {e}")
            raise

    def stop(self):
        """Stop IMU reading."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

        if self.serial and self.serial.is_open:
            self.serial.close()

        logger.info("IMU stopped")

    def _read_loop(self):
        """Main IMU reading loop."""
        logger.info("IMU reading loop started")

        while self._running:
            try:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('ascii', errors='ignore').strip()

                    if line:
                        self._parse_data(line)

            except Exception as e:
                logger.error(f"Error reading IMU: {e}")
                time.sleep(0.1)

    def _parse_data(self, line: str):
        """
        Parse IMU data from serial line.

        Expected format: ax,ay,az,gx,gy,gz,mx,my,mz,temp

        Args:
            line: Data line from IMU
        """
        try:
            parts = line.split(',')

            if len(parts) >= 6:
                # Parse accelerometer (m/s²)
                accel_x = float(parts[0]) - self.accel_offset[0]
                accel_y = float(parts[1]) - self.accel_offset[1]
                accel_z = float(parts[2]) - self.accel_offset[2]

                # Parse gyroscope (rad/s)
                gyro_x = float(parts[3]) - self.gyro_offset[0]
                gyro_y = float(parts[4]) - self.gyro_offset[1]
                gyro_z = float(parts[5]) - self.gyro_offset[2]

                # Parse magnetometer if available
                if len(parts) >= 9:
                    mag_x = float(parts[6]) - self.mag_offset[0]
                    mag_y = float(parts[7]) - self.mag_offset[1]
                    mag_z = float(parts[8]) - self.mag_offset[2]
                else:
                    mag_x = mag_y = mag_z = 0.0

                # Parse temperature if available
                if len(parts) >= 10:
                    temp = float(parts[9])
                else:
                    temp = 0.0

                # Update current data
                with self._lock:
                    self._current_data = IMUData(
                        accel_x=accel_x,
                        accel_y=accel_y,
                        accel_z=accel_z,
                        gyro_x=gyro_x,
                        gyro_y=gyro_y,
                        gyro_z=gyro_z,
                        mag_x=mag_x,
                        mag_y=mag_y,
                        mag_z=mag_z,
                        temperature=temp,
                        timestamp=time.time()
                    )

        except Exception as e:
            logger.debug(f"Failed to parse IMU data: {e}")

    def get_data(self) -> Optional[IMUData]:
        """
        Get current IMU data.

        Returns:
            IMUData object or None if no data available
        """
        with self._lock:
            return self._current_data

    def calibrate(self, samples: int = 100, duration: float = 10.0):
        """
        Calibrate IMU by measuring offsets while stationary.

        Args:
            samples: Number of samples to collect
            duration: Maximum calibration duration in seconds
        """
        logger.info(f"Starting IMU calibration with {samples} samples")
        print("\n⚙️  IMU Calibration")
        print("   Keep sensor stationary...")
        print(f"   Collecting {samples} samples...\n")

        accel_samples = []
        gyro_samples = []
        mag_samples = []

        start_time = time.time()
        count = 0

        while count < samples and (time.time() - start_time) < duration:
            data = self.get_data()

            if data:
                accel_samples.append([data.accel_x, data.accel_y, data.accel_z])
                gyro_samples.append([data.gyro_x, data.gyro_y, data.gyro_z])
                mag_samples.append([data.mag_x, data.mag_y, data.mag_z])

                count += 1
                print(f"\rProgress: {count}/{samples}", end='', flush=True)

            time.sleep(0.01)

        if count < 10:
            logger.error("Failed to collect enough calibration samples")
            return False

        # Calculate offsets (mean of samples)
        accel_array = np.array(accel_samples)
        gyro_array = np.array(gyro_samples)

        self.accel_offset = np.mean(accel_array, axis=0)
        self.accel_offset[2] -= 9.81  # Remove gravity from Z axis

        self.gyro_offset = np.mean(gyro_array, axis=0)

        if len(mag_samples) > 0:
            mag_array = np.array(mag_samples)
            self.mag_offset = np.mean(mag_array, axis=0)

        print(f"\n\n✅ Calibration complete!")
        print(f"\n📊 Offsets:")
        print(f"   Accel: [{self.accel_offset[0]:.4f}, {self.accel_offset[1]:.4f}, {self.accel_offset[2]:.4f}]")
        print(f"   Gyro:  [{self.gyro_offset[0]:.4f}, {self.gyro_offset[1]:.4f}, {self.gyro_offset[2]:.4f}]")

        logger.info("IMU calibration successful")
        return True

    def get_acceleration(self) -> Optional[Tuple[float, float, float]]:
        """
        Get acceleration vector.

        Returns:
            Tuple of (ax, ay, az) in m/s² or None
        """
        data = self.get_data()
        if data:
            return (data.accel_x, data.accel_y, data.accel_z)
        return None

    def get_angular_velocity(self) -> Optional[Tuple[float, float, float]]:
        """
        Get angular velocity vector.

        Returns:
            Tuple of (wx, wy, wz) in rad/s or None
        """
        data = self.get_data()
        if data:
            return (data.gyro_x, data.gyro_y, data.gyro_z)
        return None

    def get_orientation(self) -> Optional[Tuple[float, float, float]]:
        """
        Get orientation angles (roll, pitch, yaw) from accelerometer and magnetometer.

        Returns:
            Tuple of (roll, pitch, yaw) in radians or None
        """
        data = self.get_data()
        if not data:
            return None

        # Calculate roll and pitch from accelerometer
        roll = np.arctan2(data.accel_y, data.accel_z)
        pitch = np.arctan2(
            -data.accel_x,
            np.sqrt(data.accel_y**2 + data.accel_z**2)
        )

        # Calculate yaw from magnetometer (if available)
        if data.mag_x != 0 or data.mag_y != 0:
            # Tilt compensation
            mag_x = data.mag_x * np.cos(pitch) + data.mag_z * np.sin(pitch)
            mag_y = (data.mag_x * np.sin(roll) * np.sin(pitch) +
                    data.mag_y * np.cos(roll) -
                    data.mag_z * np.sin(roll) * np.cos(pitch))

            yaw = np.arctan2(-mag_y, mag_x)
        else:
            yaw = 0.0

        return (roll, pitch, yaw)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Mock IMU for testing on systems without hardware
class MockIMU(IMU):
    """Mock IMU for testing purposes."""

    def __init__(self, **kwargs):
        """Initialize mock IMU."""
        logger.info("Using MockIMU for testing")
        self._current_data = IMUData(
            accel_x=0.0, accel_y=0.0, accel_z=9.81,
            gyro_x=0.0, gyro_y=0.0, gyro_z=0.0,
            mag_x=0.0, mag_y=0.0, mag_z=0.0,
            temperature=25.0,
            timestamp=time.time()
        )
        self._running = False

    def start(self):
        """Start mock IMU."""
        self._running = True
        logger.info("MockIMU started")

    def stop(self):
        """Stop mock IMU."""
        self._running = False
        logger.info("MockIMU stopped")

    def get_data(self) -> IMUData:
        """Get mock data."""
        # Add small random noise
        self._current_data.accel_x = np.random.normal(0, 0.1)
        self._current_data.accel_y = np.random.normal(0, 0.1)
        self._current_data.accel_z = np.random.normal(9.81, 0.1)
        self._current_data.gyro_x = np.random.normal(0, 0.01)
        self._current_data.gyro_y = np.random.normal(0, 0.01)
        self._current_data.gyro_z = np.random.normal(0, 0.01)
        self._current_data.timestamp = time.time()
        return self._current_data
