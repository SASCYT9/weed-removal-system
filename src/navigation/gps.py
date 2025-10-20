"""GPS module for RTK navigation."""

import serial
import pynmea2
from dataclasses import dataclass
from typing import Optional
from threading import Thread, Lock
from ..utils.logger import app_logger

logger = app_logger.get_logger(__name__)


@dataclass
class GPSData:
    """GPS data container."""
    latitude: float
    longitude: float
    altitude: float
    speed: float  # m/s
    heading: float  # degrees
    fix_quality: int  # 0=invalid, 1=GPS, 2=DGPS, 4=RTK fixed, 5=RTK float
    satellites: int
    hdop: float  # Horizontal Dilution of Precision
    timestamp: float


class GPS:
    """RTK GPS interface using u-blox ZED-F9P."""

    def __init__(
        self,
        port: str = "/dev/ttyACM0",
        baudrate: int = 38400,
        timeout: float = 1.0
    ):
        """
        Initialize GPS module.

        Args:
            port: Serial port for GPS
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

        logger.info(f"Initializing GPS on {port} at {baudrate} baud")

    def start(self):
        """Start GPS reading thread."""
        try:
            self.serial = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout
            )

            self._running = True
            self._thread = Thread(target=self._read_loop, daemon=True)
            self._thread.start()

            logger.info("GPS started successfully")

        except Exception as e:
            logger.error(f"Failed to start GPS: {e}")
            raise

    def stop(self):
        """Stop GPS reading."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

        if self.serial and self.serial.is_open:
            self.serial.close()

        logger.info("GPS stopped")

    def _read_loop(self):
        """Main GPS reading loop."""
        logger.info("GPS reading loop started")

        while self._running:
            try:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('ascii', errors='ignore').strip()

                    if line.startswith('$'):
                        self._parse_nmea(line)

            except Exception as e:
                logger.error(f"Error reading GPS: {e}")

    def _parse_nmea(self, sentence: str):
        """
        Parse NMEA sentence.

        Args:
            sentence: NMEA sentence string
        """
        try:
            msg = pynmea2.parse(sentence)

            # GGA - Fix data
            if isinstance(msg, pynmea2.GGA):
                self._update_from_gga(msg)

            # RMC - Recommended Minimum
            elif isinstance(msg, pynmea2.RMC):
                self._update_from_rmc(msg)

            # VTG - Course and speed
            elif isinstance(msg, pynmea2.VTG):
                self._update_from_vtg(msg)

        except pynmea2.ParseError as e:
            logger.debug(f"NMEA parse error: {e}")
        except Exception as e:
            logger.error(f"Error parsing NMEA: {e}")

    def _update_from_gga(self, msg: pynmea2.GGA):
        """Update data from GGA message."""
        with self._lock:
            if self._current_data is None:
                self._current_data = GPSData(
                    latitude=0, longitude=0, altitude=0,
                    speed=0, heading=0, fix_quality=0,
                    satellites=0, hdop=0, timestamp=0
                )

            if msg.latitude and msg.longitude:
                self._current_data.latitude = msg.latitude
                self._current_data.longitude = msg.longitude

            if msg.altitude:
                self._current_data.altitude = msg.altitude

            if msg.gps_qual:
                self._current_data.fix_quality = int(msg.gps_qual)

            if msg.num_sats:
                self._current_data.satellites = int(msg.num_sats)

            if msg.horizontal_dil:
                self._current_data.hdop = float(msg.horizontal_dil)

    def _update_from_rmc(self, msg: pynmea2.RMC):
        """Update data from RMC message."""
        with self._lock:
            if self._current_data is None:
                self._current_data = GPSData(
                    latitude=0, longitude=0, altitude=0,
                    speed=0, heading=0, fix_quality=0,
                    satellites=0, hdop=0, timestamp=0
                )

            if msg.latitude and msg.longitude:
                self._current_data.latitude = msg.latitude
                self._current_data.longitude = msg.longitude

            if msg.spd_over_grnd:
                # Convert knots to m/s
                self._current_data.speed = msg.spd_over_grnd * 0.514444

            if msg.true_course:
                self._current_data.heading = msg.true_course

    def _update_from_vtg(self, msg: pynmea2.VTG):
        """Update data from VTG message."""
        with self._lock:
            if self._current_data is None:
                return

            if msg.spd_over_grnd_kmph:
                # Convert km/h to m/s
                self._current_data.speed = msg.spd_over_grnd_kmph / 3.6

            if msg.true_track:
                self._current_data.heading = msg.true_track

    def get_data(self) -> Optional[GPSData]:
        """
        Get current GPS data.

        Returns:
            GPSData object or None if no data available
        """
        with self._lock:
            return self._current_data

    def has_rtk_fix(self) -> bool:
        """
        Check if GPS has RTK fixed solution.

        Returns:
            True if RTK fixed (highest accuracy)
        """
        data = self.get_data()
        return data is not None and data.fix_quality == 4

    def has_fix(self) -> bool:
        """
        Check if GPS has any valid fix.

        Returns:
            True if valid fix available
        """
        data = self.get_data()
        return data is not None and data.fix_quality > 0

    def get_position(self) -> Optional[tuple]:
        """
        Get current position.

        Returns:
            Tuple of (latitude, longitude, altitude) or None
        """
        data = self.get_data()
        if data:
            return (data.latitude, data.longitude, data.altitude)
        return None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
