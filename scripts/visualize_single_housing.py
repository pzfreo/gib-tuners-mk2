#!/usr/bin/env python3
"""Visualize complete single-housing (1-gang) assembly.

Displays:
- Frame (blue, transparent)
- Post (green)
- Wheel (orange)
- Washer (yellow)
- Screw (red)

Usage:
    python scripts/visualize_single_housing.py
    python scripts/visualize_single_housing.py --scale 2.0
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build123d import (
    Align,
    Cylinder,
    Location,
    Part,
)

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import FrameParams, Hand
from gib_tuners.components.frame import create_frame
from gib_tuners.assembly.post_wheel_assembly import create_post_wheel_assembly


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Visualize single-housing assembly")
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
    shaft = Cylinder(
        radius=1.0,  # M2 nominal
        height=length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
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

    # Create configuration with single housing
    base_config = create_default_config(scale=args.scale, hand=Hand.RIGHT)
    single_frame = replace(base_config.frame, num_housings=1)
    config = replace(base_config, frame=single_frame)

    scale = config.scale
    frame_params = config.frame
    post_params = config.string_post
    wheel_params = config.gear.wheel
    gear_params = config.gear

    print("=== Single Housing Assembly Visualization ===")
    print(f"Scale: {args.scale}x")
    print()

    # Frame dimensions
    box_outer = frame_params.box_outer * scale
    wall = frame_params.wall_thickness * scale
    total_length = frame_params.total_length * scale
    housing_centers = [c * scale for c in frame_params.housing_centers]

    print("Frame geometry:")
    print(f"  Box outer: {box_outer:.2f}mm")
    print(f"  Wall thickness: {wall:.2f}mm")
    print(f"  Total length: {total_length:.2f}mm")
    print(f"  Housing center: Y={housing_centers[0]:.2f}mm")
    print()

    # Create frame
    frame = create_frame(config)

    # Determine wheel STEP path
    wheel_step = None
    if not args.no_step:
        wheel_step = Path(__file__).parent.parent / "reference" / "wheel_m0.5_z13.step"
        if not wheel_step.exists():
            print(f"Warning: Wheel STEP not found at {wheel_step}, using placeholder")
            wheel_step = None

    # Create post + wheel assembly (at origin)
    components = create_post_wheel_assembly(config, wheel_step)
    post = components["string_post"]
    wheel = components["wheel"]

    # Position post+wheel in frame
    # Frame coordinate system:
    #   - X: Width (side-to-side)
    #   - Y: Length (along frame)
    #   - Z: Height (Z=0 at mounting plate, -Z into wood)
    #
    # Post coordinate system:
    #   - Z=0 at bottom of DD section
    #   - Post extends upward in +Z
    #
    # The post must be positioned so:
    #   - Its bearing section passes through the mounting plate hole
    #   - The DD section (with wheel) is inside the frame cavity
    #   - The visible post and cap are above the frame

    # Frame cavity spans Z=-wall to Z=-box_outer+wall
    # Bottom of frame is at Z=-box_outer
    # Wheel inlet hole is at Z=-box_outer (bottom face)

    # Post position calculations:
    # Center distance offset (post toward -Y from housing center)
    center_distance = gear_params.center_distance * scale
    extra_backlash = gear_params.extra_backlash * scale
    effective_cd = center_distance - extra_backlash
    post_y_offset = -effective_cd / 2

    housing_y = housing_centers[0]
    post_y = housing_y + post_y_offset

    # Z position: align bearing section with mounting plate
    # Post bearing starts at Z = dd_cut_length (after DD section)
    # Frame mounting plate is at Z=0 with thickness = wall
    # Bearing should sit in the mounting plate hole
    dd_length = post_params.dd_cut_length * scale
    bearing_length = post_params.bearing_length * scale

    # Position so bottom of bearing is at Z=-wall (inside of mounting plate)
    # This means bottom of DD section is at Z = -wall - dd_length
    post_z = -wall - dd_length + bearing_length

    # Actually, let's think about this more carefully:
    # - Mounting plate is from Z=0 (top) to Z=-wall (inside)
    # - Post bearing section has length = bearing_length
    # - We want bearing section to fill the mounting plate hole
    # - Bearing starts at Z=dd_length on the post
    # - So post Z=dd_length should align with frame Z=0 (top of mounting plate)
    # - Therefore post origin (Z=0) should be at frame Z = -dd_length

    # But we also need the wheel to fit in the cavity...
    # Wheel is centered on DD section, which is 6mm tall
    # Frame inner cavity bottom is at Z = -box_outer + wall
    # Let's position the post so the wheel clears the bottom

    # Wheel sits from post Z=0 to Z=face_width (6mm)
    # Frame cavity floor is at Z = -box_outer + wall
    # Wheel inlet hole is 8mm diameter, so wheel (7.5mm) can pass through

    # For assembly: wheel goes in from bottom, slides up onto DD
    # Position so bottom of wheel (post Z=0) is at or above frame cavity floor
    # Frame cavity floor: Z = -box_outer + wall = -10 + 1 = -9mm

    # But we need bearing in the hole, so let's work from the top:
    # Bearing sits in mounting plate hole
    # Frame: Z=0 is top of mounting plate
    # Post: bearing starts at Z=dd_length, ends at Z=dd_length+bearing_length
    # Aligning: post Z=dd_length = frame Z=-wall (inside of mounting plate)
    # So post origin = frame Z = -wall - dd_length

    post_z = -wall  # Bottom of bearing at inside of mounting plate
    # Actually: post_z is where post Z=0 maps to frame Z
    # If bearing starts at post Z=dd_length and should be at frame Z=-wall (inner surface)
    # Then post Z=0 is at frame Z = -wall - dd_length

    post_z_offset = -wall - dd_length + bearing_length
    # Hmm, let me reconsider. The bearing section:
    # - Starts at post Z = dd_length
    # - Has length = bearing_length = 1mm (same as wall thickness)
    # - Should pass through mounting plate hole from Z=0 (top) to Z=-wall (bottom)
    # - So post Z=dd_length should = frame Z=-wall (inner surface)
    # - And post Z=dd_length+bearing_length = frame Z=0 (top surface)

    # This means: frame_Z = post_Z - dd_length - bearing_length + 0
    # Or: post_Z = frame_Z + dd_length + bearing_length
    # If frame_Z = 0 (top surface) should equal post_Z = dd_length + bearing_length
    # Then post origin (post_Z=0) is at frame_Z = -(dd_length + bearing_length)
    # Wait, that doesn't seem right either...

    # Let me be very explicit:
    # POST (at local origin):
    #   Z=0: bottom of DD section
    #   Z=dd_length: top of DD section, bottom of bearing
    #   Z=dd_length+bearing_length: top of bearing, bottom of visible post
    #   ...continues up

    # FRAME:
    #   Z=0: top surface of mounting plate
    #   Z=-wall: inner surface of mounting plate (cavity ceiling)
    #   Z=-box_outer: bottom of frame
    #   Z=-box_outer+wall: cavity floor

    # ASSEMBLY:
    # Bearing fills the mounting plate hole, so:
    #   post Z=dd_length+bearing_length aligns with frame Z=0 (top)
    #   post Z=dd_length aligns with frame Z=-wall (inner)

    # So post_local_Z + offset = frame_Z
    # dd_length + bearing_length + offset = 0
    # offset = -(dd_length + bearing_length)

    post_z_offset = -(dd_length + bearing_length)

    print("Post position in frame:")
    print(f"  Post X: 0 (centered)")
    print(f"  Post Y: {post_y:.2f}mm (housing center {housing_y:.2f} + offset {post_y_offset:.2f})")
    print(f"  Post Z offset: {post_z_offset:.2f}mm")
    print()
    print("  DD section: Z={:.2f} to Z={:.2f}".format(
        post_z_offset, post_z_offset + dd_length))
    print("  Bearing:    Z={:.2f} to Z={:.2f}".format(
        post_z_offset + dd_length, post_z_offset + dd_length + bearing_length))
    print("  Frame cavity: Z={:.2f} to Z={:.2f}".format(
        -box_outer + wall, -wall))
    print()

    # Position post and wheel
    post = post.locate(Location((0, post_y, post_z_offset)))
    wheel = wheel.locate(Location((0, post_y, post_z_offset)))

    # Create and position hardware
    face_width = wheel_params.face_width * scale
    washer_od = 5.0 * scale
    washer_id = 2.2 * scale
    washer_t = 0.5 * scale
    screw_length = 4.0 * scale
    screw_head_h = 1.5 * scale

    # Washer sits below wheel
    washer = create_washer(washer_od, washer_id, washer_t)
    washer_z = post_z_offset - washer_t
    washer = washer.locate(Location((0, post_y, washer_z)))

    # Screw threads into tap bore from below
    screw = create_m2_screw(screw_length)
    screw_z = washer_z - screw_head_h
    screw = screw.locate(Location((0, post_y, screw_z)))

    print("Hardware positions:")
    print(f"  Washer: Z={washer_z:.2f}")
    print(f"  Screw head: Z={screw_z:.2f}")
    print()

    # Check clearances
    wheel_bottom_z = post_z_offset
    cavity_floor_z = -box_outer + wall
    clearance = wheel_bottom_z - cavity_floor_z
    print(f"Wheel bottom to cavity floor clearance: {clearance:.2f}mm")

    # Show components with distinct colors
    show_object(frame, name="Frame", options={"color": (0.3, 0.5, 1), "alpha": 0.3})  # Blue, transparent
    show_object(post, name="String_post", options={"color": (0, 0.8, 0)})  # Green
    show_object(wheel, name="Wheel", options={"color": (1, 0.6, 0)})  # Orange
    show_object(washer, name="Washer", options={"color": (1, 1, 0)})  # Yellow
    show_object(screw, name="M2_screw", options={"color": (1, 0.2, 0.2)})  # Red

    print()
    print("Visualization sent to OCP viewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
