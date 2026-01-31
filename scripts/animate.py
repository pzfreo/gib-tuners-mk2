#!/usr/bin/env python3
"""Animate worm gear mechanism.

Shows tuner assembly with the worm (peg head) driving the wheel.
Uses bd_animation library with OCP CAD Viewer.

Usage:
    python scripts/animate.py                    # Default: 1-gang RH
    python scripts/animate.py -n 5               # 5-gang animation
    python scripts/animate.py --hand both        # L & R side by side
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
    python scripts/animate.py                  # 1-gang RH, 10 worm revs
    python scripts/animate.py -n 5             # 5-gang animation
    python scripts/animate.py --hand both      # L & R side by side
    python scripts/animate.py --worm-revs 1    # Single worm revolution
    python scripts/animate.py --scale 2.0      # 2x prototype scale
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
        default=10.0,
        help="Number of worm revolutions (default: 10 = 1 wheel rev for 10:1 ratio)",
    )
    parser.add_argument(
        "--hand",
        choices=["right", "left", "both"],
        default="right",
        help="Hand variant (default: right). 'both' shows L & R side by side",
    )
    parser.add_argument(
        "-n", "--num-housings",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help="Number of housings (default: 1)",
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

    # Determine worm Z mode from CLI flags
    if args.force_centered_worm:
        worm_z_mode = WormZMode.CENTERED
    elif args.force_aligned_worm:
        worm_z_mode = WormZMode.ALIGNED
    else:
        worm_z_mode = None  # Will use config default

    # Wheel/worm STEP paths
    wheel_step = gear_paths.wheel_step
    worm_step = gear_paths.worm_step
    if wheel_step is None:
        print("Warning: wheel STEP not found, using placeholder")

    gear_label = args.gear or "default"

    # Determine which hands to build
    if args.hand == "both":
        hands = [Hand.RIGHT, Hand.LEFT]
    else:
        hands = [Hand.RIGHT if args.hand == "right" else Hand.LEFT]

    print(f"=== Worm Gear Animation ({args.hand.upper()}) @ {args.scale}x [{gear_label}] ===")
    print(f"Housings: {args.num_housings}")

    # Build assemblies
    print("\nBuilding assemblies...")
    assemblies = []
    for hand in hands:
        base_config = create_default_config(
            scale=args.scale,
            hand=hand,
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )

        if worm_z_mode is not None:
            base_config = replace(
                base_config,
                gear=replace(base_config.gear, worm_z_mode=worm_z_mode),
            )

        config = replace(
            base_config,
            frame=replace(base_config.frame, num_housings=args.num_housings),
        )

        assembly = create_positioned_assembly(
            config,
            wheel_step_path=wheel_step,
            worm_step_path=worm_step,
            include_hardware=True,
        )
        assemblies.append((hand, config, assembly))

    # Use first config for common parameters
    config = assemblies[0][1]
    scale = config.scale
    ratio = config.gear.ratio

    print(f"Gear ratio: {ratio}:1")
    print(f"Worm revolutions: {args.worm_revs}")
    print(f"Wheel rotation: {args.worm_revs * 360 / ratio:.1f}°")

    # Calculate offset for side-by-side display
    frame_width = config.frame.box_outer * scale
    spacing = frame_width * 2

    # Build animation children from all assemblies
    all_children = {}

    for asm_idx, (hand, cfg, assembly) in enumerate(assemblies):
        hand_label = "rh" if hand == Hand.RIGHT else "lh"
        x_offset = asm_idx * spacing if len(assemblies) > 1 else 0
        all_parts = assembly["all_parts"]

        # Clone frame
        frame = all_parts["frame"]
        if x_offset != 0:
            frame = frame.move(Location((x_offset, 0, 0)))
        all_children[f"{hand_label}_frame"] = clone(frame, color=(0.3, 0.5, 1.0, 0.3))

        # Clone tuner parts for each housing
        for tuner_num in range(1, args.num_housings + 1):
            prefix = f"{hand_label}_t{tuner_num}"

            for part_name, color in [
                ("string_post", (0.8, 0.6, 0.3)),
                ("wheel", (0.9, 0.8, 0.2)),
                ("peg_head", (0.6, 0.4, 0.2)),
                ("peg_washer", (1, 1, 0)),
                ("peg_screw", (0.8, 0.2, 0.2)),
                ("wheel_washer", (1, 1, 0)),
                ("wheel_screw", (0.8, 0.2, 0.2)),
            ]:
                part = all_parts.get(f"{part_name}_{tuner_num}")
                if part is not None:
                    if x_offset != 0:
                        part = part.move(Location((x_offset, 0, 0)))
                    all_children[f"{prefix}_{part_name}"] = clone(part, color=color)

    # Create animation group
    anim_group = AnimationGroup(
        children=all_children,
        label="tuners",
    )

    # Create animation
    animation = Animation(anim_group)

    # Define tracks
    steps = args.steps
    duration = args.duration
    time_track = np.linspace(0, duration, steps + 1).tolist()

    # For full wheel rotation: worm does 'ratio' rotations, wheel does 1
    worm_total_deg = args.worm_revs * 359.9
    wheel_total_deg = args.worm_revs * 359.9 / ratio

    # Add tracks for each assembly and tuner
    for asm_idx, (hand, cfg, assembly) in enumerate(assemblies):
        hand_label = "rh" if hand == Hand.RIGHT else "lh"

        # Direction depends on hand
        worm_direction = -1 if hand == Hand.RIGHT else 1
        wheel_direction = -1 if hand == Hand.RIGHT else 1

        worm_track = (np.linspace(0, worm_total_deg, steps + 1) * worm_direction).tolist()
        wheel_track = (np.linspace(0, wheel_total_deg, steps + 1) * wheel_direction).tolist()

        for tuner_num in range(1, args.num_housings + 1):
            prefix = f"/tuners/{hand_label}_t{tuner_num}"

            # Peg head and hardware rotate around X axis
            animation.add_track(f"{prefix}_peg_head", "rx", time_track, worm_track)
            if f"{hand_label}_t{tuner_num}_peg_washer" in all_children:
                animation.add_track(f"{prefix}_peg_washer", "rx", time_track, worm_track)
            if f"{hand_label}_t{tuner_num}_peg_screw" in all_children:
                animation.add_track(f"{prefix}_peg_screw", "rx", time_track, worm_track)

            # Wheel and string post rotate around Z axis
            animation.add_track(f"{prefix}_wheel", "rz", time_track, wheel_track)
            animation.add_track(f"{prefix}_string_post", "rz", time_track, wheel_track)

    print(f"\nAnimation: {duration}s, {steps} steps")
    print("Sending to OCP viewer...")

    # Show and animate
    show(anim_group)
    animation.animate(speed=1)

    print("Animation started. Use OCP viewer controls to replay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
