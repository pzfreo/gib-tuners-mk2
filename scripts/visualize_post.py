#!/usr/bin/env python3
"""Visualize string post geometry with sections labeled.

Displays the string post with each section in a distinct color:
- DD section (green) - mates with wheel
- Bearing (blue) - runs in frame
- Visible post (orange) - above frame
- Cap (red) - decorative top
- M2 tap bore visible

Usage:
    python scripts/visualize_post.py
    python scripts/visualize_post.py --scale 2.0
"""

import argparse
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build123d import (
    Align,
    Axis,
    Cylinder,
    Location,
    Part,
)

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
from gib_tuners.features.dd_cut import create_dd_cut_shaft


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Visualize string post sections")
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Geometry scale factor (default: 1.0)",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Import ocp_vscode for visualization
    try:
        from ocp_vscode import show_object
    except ImportError:
        print("Error: ocp-vscode not installed. Install with: pip install ocp-vscode")
        return 1

    # Create configuration
    config = create_default_config(scale=args.scale, hand=Hand.RIGHT)
    params = config.string_post
    scale = config.scale

    # Scaled dimensions
    cap_d = params.cap_diameter * scale
    cap_h = params.cap_height * scale
    post_d = params.post_diameter * scale
    post_h = params.post_height * scale
    bearing_d = params.bearing_diameter * scale
    bearing_h = params.bearing_length * scale
    dd_length = params.dd_cut_length * scale
    tap_bore_d = 1.6 * scale  # M2 tap drill size
    tap_bore_depth = params.thread_length * scale
    string_hole_d = params.string_hole_diameter * scale
    string_hole_pos = params.string_hole_position * scale

    print("=== String Post Visualization ===")
    print(f"Scale: {args.scale}x")
    print()
    print("Post sections (from bottom to top):")

    # Build sections from bottom up
    z = 0.0

    # DD section (green) - mates with wheel
    dd_params = params.dd_cut
    dd_section = create_dd_cut_shaft(dd_params, dd_length, scale)
    dd_section = dd_section.locate(Location((0, 0, z)))
    print(f"  DD section (green):     Z={z:.2f} to Z={z + dd_length:.2f}mm (mates with wheel)")
    z += dd_length

    # Bearing section (blue) - runs in frame
    bearing = Cylinder(
        radius=bearing_d / 2,
        height=bearing_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bearing = bearing.locate(Location((0, 0, z)))
    print(f"  Bearing (blue):         Z={z:.2f} to Z={z + bearing_h:.2f}mm (in frame wall)")
    z += bearing_h

    # Visible post section (orange) - above frame
    post = Cylinder(
        radius=post_d / 2,
        height=post_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    post = post.locate(Location((0, 0, z)))
    print(f"  Visible post (orange):  Z={z:.2f} to Z={z + post_h:.2f}mm (above frame)")

    # String hole position
    hole_z = z + string_hole_pos
    print(f"    String hole at:       Z={hole_z:.2f}mm (d={string_hole_d:.2f}mm)")
    z += post_h

    # Cap (red) - decorative top
    cap = Cylinder(
        radius=cap_d / 2,
        height=cap_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cap = cap.locate(Location((0, 0, z)))
    print(f"  Cap (red):              Z={z:.2f} to Z={z + cap_h:.2f}mm (decorative)")
    z += cap_h

    print()
    print(f"Total length: {params.total_length * scale:.2f}mm")
    print()
    print("M2 tap bore (from bottom):")
    print(f"  Diameter: {tap_bore_d:.2f}mm (M2 tap drill)")
    print(f"  Depth:    {tap_bore_depth:.2f}mm")
    print()
    print("DD cut parameters:")
    print(f"  Diameter:      {dd_params.diameter * scale:.2f}mm")
    print(f"  Across flats:  {dd_params.across_flats * scale:.2f}mm")
    print(f"  Flat depth:    {dd_params.flat_depth * scale:.2f}mm")

    # Create M2 tap bore representation (cylinder showing the bore)
    tap_bore = Cylinder(
        radius=tap_bore_d / 2,
        height=tap_bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    tap_bore = tap_bore.locate(Location((0, 0, 0)))

    # Create string hole representation
    string_hole = Cylinder(
        radius=string_hole_d / 2,
        height=cap_d + 2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    string_hole = string_hole.rotate(Axis.X, 90)
    frame_top_z = dd_length + bearing_h
    string_hole = string_hole.locate(Location((0, 0, frame_top_z + string_hole_pos)))

    # Show each section with distinct colors
    show_object(dd_section, name="DD_section", options={"color": (0, 0.8, 0)})  # Green
    show_object(bearing, name="Bearing", options={"color": (0, 0.5, 1)})  # Blue
    show_object(post, name="Visible_post", options={"color": (1, 0.6, 0)})  # Orange
    show_object(cap, name="Cap", options={"color": (1, 0.2, 0.2)})  # Red

    # Show tap bore and string hole in different colors (as negative space indicators)
    show_object(tap_bore, name="M2_tap_bore", options={"color": (0.3, 0.3, 0.3), "alpha": 0.5})  # Gray
    show_object(string_hole, name="String_hole", options={"color": (0.3, 0.3, 0.3), "alpha": 0.5})  # Gray

    print()
    print("Visualization sent to OCP viewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
