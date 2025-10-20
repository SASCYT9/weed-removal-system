#!/usr/bin/env python3
"""
GPS testing and calibration utility.

This script tests RTK GPS functionality and provides diagnostic information.
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.navigation.gps import GPS
from src.utils.logger import app_logger

logger = app_logger.get_logger(__name__)


class GPSTester:
    """GPS testing and diagnostics."""

    def __init__(self, port: str = '/dev/ttyACM0', baudrate: int = 38400):
        """
        Initialize GPS tester.

        Args:
            port: Serial port for GPS
            baudrate: Serial baudrate
        """
        self.gps = GPS(port=port, baudrate=baudrate)

    def test_connection(self, duration: int = 10):
        """
        Test GPS connection and data reception.

        Args:
            duration: Test duration in seconds
        """
        print(f"\n📡 GPS Connection Test")
        print(f"   Port: {self.gps.port}")
        print(f"   Baudrate: {self.gps.baudrate}")
        print(f"   Duration: {duration}s\n")

        try:
            self.gps.start()

            start_time = time.time()
            last_data = None
            data_count = 0

            while time.time() - start_time < duration:
                data = self.gps.get_data()

                if data and data != last_data:
                    data_count += 1
                    last_data = data

                    # Display data
                    fix_quality_text = {
                        0: "No Fix",
                        1: "GPS Fix",
                        2: "DGPS Fix",
                        4: "RTK Fixed",
                        5: "RTK Float"
                    }.get(data.fix_quality, f"Unknown ({data.fix_quality})")

                    print(f"\r[{time.time()-start_time:.1f}s] "
                          f"Fix: {fix_quality_text} | "
                          f"Sats: {data.satellites} | "
                          f"HDOP: {data.hdop:.2f} | "
                          f"Lat: {data.latitude:.6f} | "
                          f"Lon: {data.longitude:.6f}",
                          end='', flush=True)

                time.sleep(0.1)

            self.gps.stop()

            print(f"\n\n✅ Connection test complete")
            print(f"   Data updates: {data_count}")
            print(f"   Update rate: {data_count/duration:.1f} Hz")

            if data_count == 0:
                print(f"\n❌ No data received - check connections!")
            elif data_count < 5:
                print(f"\n⚠️  Low update rate - check GPS antenna!")

            return data_count > 0

        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False

    def monitor_rtk(self, duration: int = 60):
        """
        Monitor RTK fix quality.

        Args:
            duration: Monitoring duration in seconds
        """
        print(f"\n🛰️  RTK GPS Monitor")
        print(f"   Duration: {duration}s")
        print(f"   Waiting for RTK fix...\n")

        try:
            self.gps.start()

            start_time = time.time()
            rtk_fixes = 0
            total_updates = 0

            while time.time() - start_time < duration:
                data = self.gps.get_data()

                if data:
                    total_updates += 1

                    if data.fix_quality == 4:  # RTK Fixed
                        rtk_fixes += 1

                    # Create status bar
                    elapsed = time.time() - start_time
                    progress = int((elapsed / duration) * 50)
                    bar = '█' * progress + '░' * (50 - progress)

                    fix_quality_text = {
                        0: "No Fix",
                        1: "GPS",
                        2: "DGPS",
                        4: "RTK-Fixed",
                        5: "RTK-Float"
                    }.get(data.fix_quality, "Unknown")

                    print(f"\r[{bar}] {elapsed:.0f}s | "
                          f"Fix: {fix_quality_text:10s} | "
                          f"Sats: {data.satellites:2d} | "
                          f"RTK: {rtk_fixes}/{total_updates}",
                          end='', flush=True)

                time.sleep(0.5)

            self.gps.stop()

            print(f"\n\n📊 RTK Statistics:")
            print(f"   Total updates: {total_updates}")
            print(f"   RTK Fixed: {rtk_fixes}")
            print(f"   RTK Rate: {rtk_fixes/total_updates*100:.1f}%")

            if rtk_fixes == 0:
                print(f"\n⚠️  No RTK fix achieved")
                print(f"   - Check RTK base station connection")
                print(f"   - Ensure clear sky view")
                print(f"   - Wait longer for fix acquisition")

        except Exception as e:
            print(f"\n❌ Error: {e}")

    def log_position(self, duration: int = 300, output_file: str = None):
        """
        Log GPS position for accuracy analysis.

        Args:
            duration: Logging duration in seconds
            output_file: Output CSV file path
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/gps_log_{timestamp}.csv"

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n📝 GPS Position Logging")
        print(f"   Duration: {duration}s")
        print(f"   Output: {output_file}\n")

        try:
            self.gps.start()

            with open(output_path, 'w') as f:
                # Write header
                f.write("timestamp,latitude,longitude,altitude,fix_quality,satellites,hdop,speed,heading\n")

                start_time = time.time()
                log_count = 0

                while time.time() - start_time < duration:
                    data = self.gps.get_data()

                    if data:
                        timestamp = datetime.now().isoformat()

                        f.write(f"{timestamp},"
                               f"{data.latitude},"
                               f"{data.longitude},"
                               f"{data.altitude},"
                               f"{data.fix_quality},"
                               f"{data.satellites},"
                               f"{data.hdop},"
                               f"{data.speed},"
                               f"{data.heading}\n")

                        log_count += 1

                        # Display progress
                        elapsed = time.time() - start_time
                        print(f"\r[{elapsed:.0f}s] Logged {log_count} positions", end='', flush=True)

                    time.sleep(1.0)

            self.gps.stop()

            print(f"\n\n✅ Logging complete")
            print(f"   Positions logged: {log_count}")
            print(f"   File: {output_path}")

        except Exception as e:
            print(f"\n❌ Error: {e}")

    def analyze_accuracy(self, log_file: str):
        """
        Analyze GPS accuracy from log file.

        Args:
            log_file: Path to GPS log CSV file
        """
        print(f"\n📊 GPS Accuracy Analysis")
        print(f"   Log file: {log_file}\n")

        try:
            import pandas as pd
            import numpy as np

            # Read log file
            df = pd.read_csv(log_file)

            if len(df) < 10:
                print("❌ Not enough data for analysis (need at least 10 points)")
                return

            # Calculate statistics
            lat_mean = df['latitude'].mean()
            lat_std = df['latitude'].std()
            lon_mean = df['longitude'].mean()
            lon_std = df['longitude'].std()
            alt_mean = df['altitude'].mean()
            alt_std = df['altitude'].std()

            # Convert std to meters (approximate)
            # 1 degree latitude ≈ 111 km
            lat_std_m = lat_std * 111000
            lon_std_m = lon_std * 111000 * np.cos(np.radians(lat_mean))

            # Calculate 2D RMS error
            rms_2d = np.sqrt(lat_std_m**2 + lon_std_m**2)

            print(f"📍 Position Statistics:")
            print(f"   Mean Latitude: {lat_mean:.8f}°")
            print(f"   Mean Longitude: {lon_mean:.8f}°")
            print(f"   Mean Altitude: {alt_mean:.2f}m")
            print(f"\n📏 Accuracy (Standard Deviation):")
            print(f"   Latitude: {lat_std_m:.3f}m ({lat_std*3600:.2f}\")")
            print(f"   Longitude: {lon_std_m:.3f}m ({lon_std*3600:.2f}\")")
            print(f"   Altitude: {alt_std:.3f}m")
            print(f"   2D RMS: {rms_2d:.3f}m")

            # RTK quality statistics
            if 'fix_quality' in df.columns:
                rtk_fixed = (df['fix_quality'] == 4).sum()
                rtk_float = (df['fix_quality'] == 5).sum()
                dgps = (df['fix_quality'] == 2).sum()
                gps = (df['fix_quality'] == 1).sum()

                print(f"\n📡 Fix Quality Distribution:")
                print(f"   RTK Fixed: {rtk_fixed} ({rtk_fixed/len(df)*100:.1f}%)")
                print(f"   RTK Float: {rtk_float} ({rtk_float/len(df)*100:.1f}%)")
                print(f"   DGPS: {dgps} ({dgps/len(df)*100:.1f}%)")
                print(f"   GPS: {gps} ({gps/len(df)*100:.1f}%)")

            # HDOP statistics
            if 'hdop' in df.columns:
                hdop_mean = df['hdop'].mean()
                print(f"\n📊 HDOP:")
                print(f"   Mean: {hdop_mean:.2f}")
                print(f"   Min: {df['hdop'].min():.2f}")
                print(f"   Max: {df['hdop'].max():.2f}")

        except ImportError:
            print("❌ pandas required for analysis")
            print("Install with: pip install pandas")
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='GPS testing and calibration utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test GPS connection
  python test_gps.py test --duration 10

  # Monitor RTK fix
  python test_gps.py monitor --duration 60

  # Log GPS positions for accuracy analysis
  python test_gps.py log --duration 300

  # Analyze logged data
  python test_gps.py analyze --log-file data/gps_log_20240101_120000.csv
        """
    )

    parser.add_argument('--port', default='/dev/ttyACM0', help='GPS serial port')
    parser.add_argument('--baudrate', type=int, default=38400, help='Serial baudrate')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test GPS connection')
    test_parser.add_argument('--duration', type=int, default=10, help='Test duration (seconds)')

    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor RTK fix')
    monitor_parser.add_argument('--duration', type=int, default=60, help='Monitor duration (seconds)')

    # Log command
    log_parser = subparsers.add_parser('log', help='Log GPS positions')
    log_parser.add_argument('--duration', type=int, default=300, help='Log duration (seconds)')
    log_parser.add_argument('--output', help='Output CSV file')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze GPS accuracy')
    analyze_parser.add_argument('--log-file', required=True, help='GPS log CSV file')

    args = parser.parse_args()

    # Setup logging
    app_logger.setup(log_level='INFO')

    if args.command == 'test':
        tester = GPSTester(args.port, args.baudrate)
        tester.test_connection(args.duration)

    elif args.command == 'monitor':
        tester = GPSTester(args.port, args.baudrate)
        tester.monitor_rtk(args.duration)

    elif args.command == 'log':
        tester = GPSTester(args.port, args.baudrate)
        tester.log_position(args.duration, args.output)

    elif args.command == 'analyze':
        tester = GPSTester(args.port, args.baudrate)
        tester.analyze_accuracy(args.log_file)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
