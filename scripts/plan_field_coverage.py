#!/usr/bin/env python3
"""
Field coverage path planning utility.

Generate and visualize optimal coverage patterns for field weeding.
"""

import sys
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.planning.field_coverage import FieldCoveragePlanner, FieldBoundary
from src.utils.logger import app_logger

logger = app_logger.get_logger(__name__)


def visualize_path(
    field: FieldBoundary,
    waypoints: list,
    title: str = "Field Coverage Path",
    save_to: str = None
):
    """
    Visualize coverage path.

    Args:
        field: Field boundary
        waypoints: List of waypoints
        title: Plot title
        save_to: Save figure to file (optional)
    """
    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot field boundary
    corners = np.array(field.corners + [field.corners[0]])  # Close the polygon
    ax.plot(corners[:, 0], corners[:, 1], 'k-', linewidth=2, label='Field Boundary')

    # Plot waypoints and path
    if waypoints:
        waypoints_array = np.array(waypoints)
        ax.plot(waypoints_array[:, 0], waypoints_array[:, 1],
               'b-', linewidth=1, alpha=0.6, label='Coverage Path')
        ax.plot(waypoints_array[:, 0], waypoints_array[:, 1],
               'ro', markersize=3, alpha=0.5)

        # Mark start and end
        ax.plot(waypoints[0][0], waypoints[0][1],
               'go', markersize=15, label='Start', zorder=10)
        ax.plot(waypoints[-1][0], waypoints[-1][1],
               'rs', markersize=15, label='End', zorder=10)

    ax.set_xlabel('X (meters)')
    ax.set_ylabel('Y (meters)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axis('equal')

    if save_to:
        plt.savefig(save_to, dpi=150, bbox_inches='tight')
        print(f"\n💾 Path visualization saved to: {save_to}")

    plt.show()


def create_rectangular_field(
    width: float = 50.0,
    length: float = 100.0,
    center_x: float = 0.0,
    center_y: float = 0.0
) -> FieldBoundary:
    """
    Create a rectangular field boundary.

    Args:
        width: Field width in meters
        length: Field length in meters
        center_x: Center X coordinate
        center_y: Center Y coordinate

    Returns:
        FieldBoundary object
    """
    half_width = width / 2
    half_length = length / 2

    corners = [
        (center_x - half_width, center_y - half_length),  # Bottom-left
        (center_x + half_width, center_y - half_length),  # Bottom-right
        (center_x + half_width, center_y + half_length),  # Top-right
        (center_x - half_width, center_y + half_length),  # Top-left
    ]

    return FieldBoundary(corners=corners)


def create_polygon_field(corners: list) -> FieldBoundary:
    """
    Create a polygon field boundary from corner coordinates.

    Args:
        corners: List of (x, y) tuples

    Returns:
        FieldBoundary object
    """
    return FieldBoundary(corners=corners)


def calculate_path_stats(waypoints: list, robot_width: float):
    """
    Calculate and display path statistics.

    Args:
        waypoints: List of waypoints
        robot_width: Robot width in meters
    """
    if not waypoints:
        return

    # Calculate total distance
    total_distance = 0.0
    for i in range(len(waypoints) - 1):
        p1 = np.array(waypoints[i])
        p2 = np.array(waypoints[i+1])
        total_distance += np.linalg.norm(p2 - p1)

    # Calculate coverage area
    coverage_area = total_distance * robot_width

    # Estimate time (assuming 0.5 m/s speed)
    speed = 0.5  # m/s
    time_seconds = total_distance / speed
    time_minutes = time_seconds / 60

    print(f"\n📊 Path Statistics:")
    print(f"   Waypoints: {len(waypoints)}")
    print(f"   Total distance: {total_distance:.1f} m")
    print(f"   Coverage area: {coverage_area:.1f} m²")
    print(f"   Estimated time: {time_minutes:.1f} minutes (at {speed} m/s)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Field coverage path planning',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate boustrophedon pattern for 50x100m field
  python plan_field_coverage.py --width 50 --length 100 --pattern boustrophedon

  # Generate spiral pattern
  python plan_field_coverage.py --width 50 --length 100 --pattern spiral

  # Rotate pattern by 45 degrees
  python plan_field_coverage.py --width 50 --length 100 --angle 45

  # Save path to file
  python plan_field_coverage.py --width 50 --length 100 --output data/path.json

  # Custom polygon field
  python plan_field_coverage.py --polygon "0,0 50,0 50,100 0,100" --pattern boustrophedon
        """
    )

    # Field definition
    parser.add_argument('--width', type=float, default=50.0, help='Field width (meters)')
    parser.add_argument('--length', type=float, default=100.0, help='Field length (meters)')
    parser.add_argument('--polygon', type=str, help='Custom polygon corners "x1,y1 x2,y2 ..."')

    # Robot parameters
    parser.add_argument('--robot-width', type=float, default=0.5, help='Robot width (meters)')
    parser.add_argument('--overlap', type=float, default=0.1, help='Pass overlap (meters)')
    parser.add_argument('--headland', type=float, default=2.0, help='Headland width (meters)')

    # Pattern parameters
    parser.add_argument(
        '--pattern',
        type=str,
        default='boustrophedon',
        choices=['boustrophedon', 'spiral', 'zigzag'],
        help='Coverage pattern'
    )
    parser.add_argument('--angle', type=float, default=0.0, help='Pattern angle (degrees)')
    parser.add_argument('--spiral-direction', type=str, default='inward',
                       choices=['inward', 'outward'], help='Spiral direction')

    # Optimization
    parser.add_argument('--optimize', action='store_true', help='Optimize waypoint order')
    parser.add_argument('--smooth-turns', action='store_true', help='Add smooth headland turns')
    parser.add_argument('--turn-radius', type=float, default=1.0, help='Turn radius (meters)')

    # Output
    parser.add_argument('--output', type=str, help='Save path to JSON file')
    parser.add_argument('--save-plot', type=str, help='Save visualization to image file')
    parser.add_argument('--no-plot', action='store_true', help='Do not show plot')

    args = parser.parse_args()

    # Setup logging
    app_logger.setup(log_level='INFO')

    # Create field boundary
    if args.polygon:
        # Parse polygon corners
        try:
            corners_str = args.polygon.split()
            corners = [tuple(map(float, c.split(','))) for c in corners_str]
            field = create_polygon_field(corners)
            print(f"\n🗺️  Using polygon field with {len(corners)} corners")
        except Exception as e:
            print(f"❌ Error parsing polygon: {e}")
            return
    else:
        field = create_rectangular_field(args.width, args.length)
        print(f"\n🗺️  Using rectangular field: {args.width}m x {args.length}m")

    # Create planner
    planner = FieldCoveragePlanner(
        robot_width=args.robot_width,
        overlap=args.overlap,
        headland_width=args.headland
    )

    # Generate path
    print(f"\n🛤️  Generating {args.pattern} coverage pattern...")

    if args.pattern == 'spiral':
        waypoints = planner.spiral_pattern(field, direction=args.spiral_direction)
    else:
        waypoints = planner.parallel_lines(field, angle=args.angle, pattern=args.pattern)

    if not waypoints:
        print("❌ Failed to generate path")
        return

    # Optimize if requested
    if args.optimize:
        print("\n🔧 Optimizing path...")
        waypoints = planner.optimize_path(waypoints)

    # Add smooth turns if requested
    if args.smooth_turns:
        print("\n🔄 Adding smooth turns...")
        waypoints = planner.add_headland_turns(waypoints, turn_radius=args.turn_radius)

    # Calculate statistics
    calculate_path_stats(waypoints, args.robot_width)

    # Save path if requested
    if args.output:
        planner.save_path(waypoints, args.output)
        print(f"\n💾 Path saved to: {args.output}")

    # Visualize
    if not args.no_plot:
        print("\n📊 Generating visualization...")
        title = f"{args.pattern.capitalize()} Pattern - {len(waypoints)} waypoints"
        visualize_path(field, waypoints, title=title, save_to=args.save_plot)

    print("\n✅ Path planning complete!")


if __name__ == '__main__':
    main()
