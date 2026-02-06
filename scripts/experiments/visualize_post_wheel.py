#!/usr/bin/env python3
"""Visualize post + wheel assembly.

Displays:
- Post (green)
- Wheel from STEP (orange)
- Washer (yellow)
- M2 screw (red)

Usage:
    python scripts/visualize_post_wheel.py
    python scripts/visualize_post_wheel.py --scale 2.0
"""

import argparse
import sys
import warnings
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
warnings.filterwarnings("ignore", category=DeprecationWarning)

from build123d import (
    Align,
    Cylinder,
    Location,
    Part,
)

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
from gib_tuners.assembly.post_wheel_assembly import create_post_wheel_assembly


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Visualize post + wheel assembly")
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Geometry scale factor (default: 1.0)",
    )
    parser.add_argument(
        "--no-step",
        action="store_true",
        help="Use placeholder wheel instead of STEP file",
    )
    return parser.parse_args()


def create_washer(od: float, id_: float, thickness: float) -> Part:
    """Create a washer geometry."""
    outer = Cylinder(
        radius=od / 2,
        height=thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    inner = Cylinder(
        radius=id_ / 2,
        height=thickness + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    inner = inner.locate(Location((0, 0, -0.05)))
    return outer - inner


def create_m2_screw(length: float, head_d: float = 3.8, head_h: float = 1.5) -> Part:
    """Create a simplified M2 screw geometry."""
    # Screw shaft (pointing up +Z)
    shaft = Cylinder(
        radius=1.0,  # M2 nominal
        height=length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Screw head
    head = Cylinder(
        radius=head_d / 2,
        height=head_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    head = head.locate(Location((0, 0, -head_h)))
    return shaft + head


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
    scale = config.scale
    post_params = config.string_post
    wheel_params = config.gear.wheel

    # Determine wheel STEP path
    wheel_step = None
    if not args.no_step:
        wheel_step = Path(__file__).parent.parent / "reference" / "wheel_m0.5_z13.step"
        if not wheel_step.exists():
            print(f"Warning: Wheel STEP not found at {wheel_step}, using placeholder")
            wheel_step = None

    print("=== Post + Wheel Assembly Visualization ===")
    print(f"Scale: {args.scale}x")
    print()

    # Create post + wheel assembly
    components = create_post_wheel_assembly(config, wheel_step)
    post = components["string_post"]
    wheel = components["wheel"]

    # Dimensions for positioning hardware
    dd_length = post_params.dd_cut_length * scale
    face_width = wheel_params.face_width * scale

    # Hardware dimensions (typical M2)
    washer_od = 5.0 * scale
    washer_id = 2.2 * scale
    washer_t = 0.5 * scale
    screw_length = 4.0 * scale

    print("Component positions:")
    print(f"  Post:   DD section from Z=0 to Z={dd_length:.2f}mm")
    print(f"  Wheel:  Face from Z=0 to Z={face_width:.2f}mm (centered on DD)")
    print()

    # Create washer (sits below wheel at Z=0, going into -Z)
    washer = create_washer(washer_od, washer_id, washer_t)
    washer_z = -washer_t
    washer = washer.locate(Location((0, 0, washer_z)))
    print(f"  Washer: Z={washer_z:.2f} to Z=0 (OD={washer_od:.2f}mm)")

    # Create M2 screw (threads into tap bore from below)
    screw = create_m2_screw(screw_length * scale)
    # Position so head is below washer, shaft goes up into tap bore
    screw_head_h = 1.5 * scale
    screw_z = washer_z - screw_head_h
    screw = screw.locate(Location((0, 0, screw_z)))
    print(f"  Screw:  Head at Z={screw_z:.2f}, shaft into tap bore")
    print()

    # Calculate total assembly dimensions
    total_height = post_params.total_length * scale
    print(f"Post total height: {total_height:.2f}mm")
    print(f"Wheel OD: {wheel_params.tip_diameter * scale:.2f}mm")
    print(f"Center distance: {config.gear.center_distance * scale:.2f}mm")

    # Show components with distinct colors
    show_object(post, name="String_post", options={"color": (0, 0.8, 0)})  # Green
    show_object(wheel, name="Wheel", options={"color": (1, 0.6, 0)})  # Orange
    show_object(washer, name="Washer", options={"color": (1, 1, 0)})  # Yellow
    show_object(screw, name="M2_screw", options={"color": (1, 0.2, 0.2)})  # Red

    print()
    print("Visualization sent to OCP viewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
