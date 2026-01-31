#!/usr/bin/env python3
"""Animate worm gear mechanism.

Shows a 1-gang tuner with the worm (peg head) driving the wheel.
Uses bd_animation library with OCP CAD Viewer.

Usage:
    python scripts/animate.py                    # Default animation
    python scripts/animate.py --worm-revs 1      # Single worm revolution
    python scripts/animate.py --scale 2.0        # 2x scale
    python scripts/animate.py --duration 8.0     # Slower animation
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build123d import Location

from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.config.parameters import Hand, WormZMode
from gib_tuners.assembly.gang_assembly import create_positioned_assembly

REFERENCE_DIR = Path(__file__).parent.parent / "reference"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Animate worm gear mechanism",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/animate.py                  # 13 worm revs = 1 wheel rev
    python scripts/animate.py --worm-revs 1    # Single worm revolution
    python scripts/animate.py --scale 2.0      # 2x prototype scale
    python scripts/animate.py --duration 8.0   # Slower animation
        """,
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Scale factor (default: 1.0)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=8.0,
        help="Animation duration in seconds (default: 8.0)",
    )
    parser.add_argument(
        "--worm-revs",
        type=float,
        default=13.0,
        help="Number of worm revolutions (default: 13 = 1 wheel revolution)",
    )
    parser.add_argument(
        "--hand",
        choices=["right", "left"],
        default="right",
        help="Hand variant (default: right)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=180,
        help="Animation steps (default: 180)",
    )
    parser.add_argument(
        "--gear",
        type=str,
        default=None,
        help="Gear config name (e.g., 'balanced')",
    )
    worm_z_group = parser.add_mutually_exclusive_group()
    worm_z_group.add_argument(
        "--force-centered-worm",
        action="store_true",
        help="Force worm centered in frame (override globoid/hobbing auto-alignment)",
    )
    worm_z_group.add_argument(
        "--force-aligned-worm",
        action="store_true",
        help="Force worm aligned with wheel center (even for cylindrical worms)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Check for required packages
    try:
        from bd_animation import AnimationGroup, clone
        from ocp_vscode import show, Animation
    except ImportError as e:
        print(f"Error: Missing package - {e}")
        print("Install with: pip install git+https://github.com/bernhard-42/bd_animation.git")
        return 1

    # Resolve gear config paths
    gear_paths = resolve_gear_config(args.gear)

    # Create 1-gang config
    hand = Hand.RIGHT if args.hand == "right" else Hand.LEFT
    base_config = create_default_config(
        scale=args.scale,
        hand=hand,
        gear_json_path=gear_paths.json_path,
        config_dir=gear_paths.config_dir,
    )

    # Determine worm Z mode from CLI flags
    if args.force_centered_worm:
        worm_z_mode = WormZMode.CENTERED
    elif args.force_aligned_worm:
        worm_z_mode = WormZMode.ALIGNED
    else:
        worm_z_mode = base_config.gear.worm_z_mode  # AUTO (from JSON hints)

    config = replace(
        base_config,
        frame=replace(base_config.frame, num_housings=1),
        gear=replace(base_config.gear, worm_z_mode=worm_z_mode),
    )

    scale = config.scale
    ratio = config.gear.ratio

    gear_label = args.gear or "default"
    print(f"=== Worm Gear Animation ({args.hand.upper()}) @ {args.scale}x [{gear_label}] ===")
    print(f"Gear ratio: {ratio}:1")
    print(f"Worm revolutions: {args.worm_revs}")
    print(f"Wheel rotation: {args.worm_revs * 360 / ratio:.1f}°")

    # Build assembly using same code as viz.py
    print("\nBuilding assembly...")
    wheel_step = gear_paths.wheel_step
    worm_step = gear_paths.worm_step
    if wheel_step is None:
        print("  Warning: wheel STEP not found, using placeholder")

    assembly = create_positioned_assembly(
        config,
        wheel_step_path=wheel_step,
        worm_step_path=worm_step,
        include_hardware=True,
    )

    # Extract parts (1-gang, so tuner index is 1)
    all_parts = assembly["all_parts"]
    frame = all_parts["frame"]
    string_post = all_parts["string_post_1"]
    wheel = all_parts["wheel_1"]
    peg_head = all_parts["peg_head_1"]
    peg_washer = all_parts.get("peg_washer_1")
    peg_screw = all_parts.get("peg_screw_1")
    wheel_washer = all_parts.get("wheel_washer_1")
    wheel_screw = all_parts.get("wheel_screw_1")

    # Calculate pivot points for animation from config
    # These must match the positioning in tuner_unit.py
    frame_params = config.frame
    post_params = config.string_post
    gear_params = config.gear

    # Wheel pivot: Z-axis at wheel center
    dd_h = post_params.dd_cut_length * scale
    bearing_h = post_params.bearing_length * scale
    post_z_offset = -(dd_h + bearing_h)
    face_width = gear_params.wheel.face_width * scale
    wheel_z = post_z_offset + face_width / 2

    # Housing Y position (1-gang)
    housing_y = assembly["housing_centers"][0]
    effective_cd = assembly["effective_cd"]
    translation_y = housing_y - effective_cd / 2

    # Peg head pivot: X-axis at worm shaft center
    box_outer = frame_params.box_outer * scale
    box_inner = frame_params.box_inner * scale
    center_distance = gear_params.center_distance * scale
    worm_length = gear_params.worm.length * scale

    half_inner = box_inner / 2
    worm_clearance = (box_inner - worm_length) / 2
    worm_z = -box_outer / 2

    if config.hand == Hand.RIGHT:
        peg_x = half_inner - worm_clearance
    else:
        peg_x = -(half_inner - worm_clearance)

    peg_y = center_distance + translation_y

    print(f"  Wheel pivot: (0, {translation_y:.2f}, {wheel_z:.2f})")
    print(f"  Peg pivot: ({peg_x:.2f}, {peg_y:.2f}, {worm_z:.2f})")

    # Clone parts for animation (no origin transform - keep positions from assembly)
    frame_cloned = clone(frame, color=(0.3, 0.5, 1.0, 0.3))  # Blue, transparent
    post_cloned = clone(string_post, color=(0.8, 0.6, 0.3))
    wheel_cloned = clone(wheel, color=(0.9, 0.8, 0.2))
    peg_cloned = clone(peg_head, color=(0.6, 0.4, 0.2))

    # Hardware
    children = {
        "frame": frame_cloned,
        "string_post": post_cloned,
        "wheel": wheel_cloned,
        "peg_head": peg_cloned,
    }

    if peg_washer:
        children["peg_washer"] = clone(peg_washer, color=(1, 1, 0))
    if peg_screw:
        children["peg_screw"] = clone(peg_screw, color=(0.8, 0.2, 0.2))
    if wheel_washer:
        children["wheel_washer"] = clone(wheel_washer, color=(1, 1, 0))
    if wheel_screw:
        children["wheel_screw"] = clone(wheel_screw, color=(0.8, 0.2, 0.2))

    # Create animation group
    anim_group = AnimationGroup(
        children=children,
        label="tuner",
    )

    # Create animation
    animation = Animation(anim_group)

    # Define tracks
    steps = args.steps
    duration = args.duration

    time_track = np.linspace(0, duration, steps + 1).tolist()
    # RH: worm rotates one way, wheel rotates CW (negative Z)
    # LH: mirror - opposite directions
    worm_direction = -1 if config.hand == Hand.RIGHT else 1
    wheel_direction = -1 if config.hand == Hand.RIGHT else 1

    # For full wheel rotation: worm does 'ratio' rotations, wheel does 1
    # Use 359.9° to avoid exact 360° boundary issues with animation looping
    worm_total_deg = args.worm_revs * 359.9
    wheel_total_deg = args.worm_revs * 359.9 / ratio

    worm_track = (np.linspace(0, worm_total_deg, steps + 1) * worm_direction).tolist()
    wheel_track = (np.linspace(0, wheel_total_deg, steps + 1) * wheel_direction).tolist()

    # Add rotation tracks
    # Peg head rotates around X axis (shaft axis)
    animation.add_track("/tuner/peg_head", "rx", time_track, worm_track)

    # Peg washer and screw rotate with peg head
    if peg_washer:
        animation.add_track("/tuner/peg_washer", "rx", time_track, worm_track)
    if peg_screw:
        animation.add_track("/tuner/peg_screw", "rx", time_track, worm_track)

    # Wheel and string post rotate together around Z axis (post axis)
    animation.add_track("/tuner/wheel", "rz", time_track, wheel_track)
    animation.add_track("/tuner/string_post", "rz", time_track, wheel_track)

    print(f"\nAnimation: {duration}s, {steps} steps")
    print("Sending to OCP viewer...")

    # Show and animate
    show(anim_group)
    animation.animate(speed=1)

    print("Animation started. Use OCP viewer controls to replay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
