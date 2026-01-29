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

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
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
        default=4.0,
        help="Animation duration in seconds (default: 4.0)",
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Check for required packages
    try:
        from bd_animation import AnimationGroup, clone, normalize_track
        from ocp_vscode import show, Animation
    except ImportError as e:
        print(f"Error: Missing package - {e}")
        print("Install with: pip install git+https://github.com/bernhard-42/bd_animation.git")
        return 1

    # Create 1-gang config
    hand = Hand.RIGHT if args.hand == "right" else Hand.LEFT
    base_config = create_default_config(scale=args.scale, hand=hand)
    config = replace(
        base_config,
        frame=replace(base_config.frame, num_housings=1)
    )

    scale = config.scale
    ratio = config.gear.ratio

    print(f"=== Worm Gear Animation ({args.hand.upper()}) @ {args.scale}x ===")
    print(f"Gear ratio: {ratio}:1")
    print(f"Worm revolutions: {args.worm_revs}")
    print(f"Wheel rotation: {args.worm_revs * 360 / ratio:.1f}°")

    # Build assembly using same code as viz.py
    print("\nBuilding assembly...")
    wheel_step = REFERENCE_DIR / "wheel_m0.5_z13.step"
    if not wheel_step.exists():
        wheel_step = None
        print("  Warning: wheel STEP not found, using placeholder")

    assembly = create_positioned_assembly(
        config,
        wheel_step_path=wheel_step,
        include_hardware=False,  # No hardware for animation
    )

    # Extract parts (1-gang, so tuner index is 1)
    all_parts = assembly["all_parts"]
    frame = all_parts["frame"]
    string_post = all_parts["string_post_1"]
    wheel = all_parts["wheel_1"]
    peg_head = all_parts["peg_head_1"]

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

    wheel_pivot = Location((0, translation_y, wheel_z))

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
    peg_pivot = Location((peg_x, peg_y, worm_z))

    print(f"  Wheel pivot: (0, {translation_y:.2f}, {wheel_z:.2f})")
    print(f"  Peg pivot: ({peg_x:.2f}, {peg_y:.2f}, {worm_z:.2f})")

    # Clone parts with proper origins for rotation
    # Static parts don't need special origin handling
    frame_cloned = clone(frame, color=(0.7, 0.7, 0.7))
    post_cloned = clone(string_post, color=(0.8, 0.6, 0.3))

    # Animated parts need origin at their rotation axis
    wheel_cloned = clone(wheel, color=(0.9, 0.8, 0.2), origin=wheel_pivot)
    peg_cloned = clone(peg_head, color=(0.6, 0.4, 0.2), origin=peg_pivot)

    # Create animation group
    anim_group = AnimationGroup(
        children={
            "frame": frame_cloned,
            "string_post": post_cloned,
            "wheel": wheel_cloned,
            "peg_head": peg_cloned,
        },
        label="tuner",
    )

    # Create animation
    animation = Animation(anim_group)

    # Define tracks
    steps = args.steps
    duration = args.duration

    time_track = np.linspace(0, duration, steps + 1)
    worm_track = np.linspace(0, args.worm_revs * 360, steps + 1)
    wheel_track = np.linspace(0, args.worm_revs * 360 / ratio, steps + 1)

    # Add rotation tracks
    # Peg head rotates around X axis (shaft axis)
    animation.add_track("/tuner/peg_head", "rx", time_track, normalize_track(worm_track))

    # Wheel rotates around Z axis (post axis)
    animation.add_track("/tuner/wheel", "rz", time_track, normalize_track(wheel_track))

    print(f"\nAnimation: {duration}s, {steps} steps")
    print("Sending to OCP viewer...")

    # Show and animate
    show(anim_group)
    animation.animate(speed=1)

    print("Animation started. Use OCP viewer controls to replay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
