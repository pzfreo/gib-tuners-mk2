#!/usr/bin/env python3
"""Animate tuner assembly process.

Shows a 1-gang RH tuner being assembled step-by-step,
following the real physical assembly sequence:
1. Worm (peg head) inserted through side wall
2. Peg washer + screw added
3. Wheel slides into frame from the open end
4. String post inserted from above
5. Wheel washer + screw fitted from below

Uses bd_animation library with OCP CAD Viewer.

Usage:
    python scripts/animate_assembly.py --gear c13
    python scripts/animate_assembly.py --gear c13 --scale 2.0
    python scripts/animate_assembly.py --gear c13 --duration 10.0
    python scripts/animate_assembly.py --gear c13 --gif assembly.gif
"""

import argparse
import sys
import warnings
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
warnings.filterwarnings("ignore", category=DeprecationWarning)

from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.config.parameters import Hand


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Animate tuner assembly process (1-gang RH)",
    )
    parser.add_argument(
        "--gear",
        type=str,
        required=True,
        help="Gear config name (e.g., 'c13')",
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
        "--steps",
        type=int,
        default=120,
        help="Animation steps (default: 120)",
    )
    parser.add_argument(
        "--gif",
        type=str,
        default=None,
        help="Save animation as GIF to this path (e.g., assembly.gif)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=25,
        help="GIF frames per second (default: 25). Best with 10, 20, 25, 50.",
    )
    return parser.parse_args()


# Assembly sequence: (part_key, axis, offset_mm, start_frac, end_frac)
# Follows real physical assembly order.
# Peg head enters from +X; washer/screw from -X (opposite side).
# Wheel enters from -Y (away from worm at +Y center_distance).
ASSEMBLY_SEQUENCE = [
    ("peg_head_1",    "tx", +30, 0.00, 0.10),
    ("peg_washer_1",  "tx", -30, 0.10, 0.18),
    ("peg_screw_1",   "tx", -30, 0.16, 0.24),
    ("wheel_1",       "ty", -30, 0.24, 0.38),
    ("string_post_1", "tz", +30, 0.38, 0.52),
    ("wheel_washer_1","tz", -20, 0.52, 0.62),
    ("wheel_screw_1", "tz", -25, 0.58, 0.68),
]

# Fraction of total duration where assembly ends and turning demo begins
ASSEMBLY_END_FRAC = 0.70
WORM_REVS = 2


def main() -> int:
    args = parse_args()

    try:
        from bd_animation import AnimationGroup, clone
        from ocp_vscode import show, Animation
    except ImportError as e:
        print(f"Error: Missing package - {e}")
        print("Install with: pip install git+https://github.com/bernhard-42/bd_animation.git")
        return 1

    gear_paths = resolve_gear_config(args.gear)

    config = create_default_config(
        scale=args.scale,
        hand=Hand.RIGHT,
        gear_json_path=gear_paths.json_path,
        config_dir=gear_paths.config_dir,
    )
    config = replace(
        config,
        frame=replace(config.frame, num_housings=1),
    )

    from gib_tuners.assembly.gang_assembly import create_positioned_assembly

    print(f"=== Assembly Animation @ {args.scale}x [{args.gear}] ===")
    print("Building assembly...")

    assembly = create_positioned_assembly(
        config,
        wheel_step_path=gear_paths.wheel_step,
        worm_step_path=gear_paths.worm_step,
        include_hardware=True,
    )

    all_parts = assembly["all_parts"]

    # Clone parts with colors
    COLOR_MAP = {
        "frame":         (0.3, 0.5, 1.0, 0.3),
        "peg_head_1":    (0.6, 0.4, 0.2),
        "peg_washer_1":  (1.0, 1.0, 0.0),
        "peg_screw_1":   (0.8, 0.2, 0.2),
        "wheel_1":       (0.9, 0.8, 0.2),
        "string_post_1": (0.8, 0.6, 0.3),
        "wheel_washer_1":(1.0, 1.0, 0.0),
        "wheel_screw_1": (0.8, 0.2, 0.2),
    }

    children = {}
    for name, part in all_parts.items():
        color = COLOR_MAP.get(name, (0.5, 0.5, 0.5))
        children[name] = clone(part, color=color)

    from ocp_vscode import Camera

    anim_group = AnimationGroup(children=children, label="assembly")
    show(anim_group, reset_camera=Camera.RESET)

    animation = Animation(anim_group)

    duration = args.duration
    scale = args.scale
    ratio = config.gear.ratio

    # --- Assembly translation tracks ---
    for part_key, axis, offset_mm, start_frac, end_frac in ASSEMBLY_SEQUENCE:
        if part_key not in children:
            continue

        offset = offset_mm * scale
        t_start = start_frac * duration
        t_end = end_frac * duration

        # 4 keyframes: hold at offset until start, slide to 0, hold through end
        times = [0, t_start, t_end, duration]
        values = [offset, offset, 0, 0]

        animation.add_track(f"/assembly/{part_key}", axis, times, values)

    # --- Turning demo after assembly (2 worm revolutions) ---
    # Use dense keyframes (same approach as animate.py)
    t_turn_start = ASSEMBLY_END_FRAC * duration
    t_turn_end = duration
    turn_steps = 180

    worm_total_deg = WORM_REVS * 359.9
    wheel_total_deg = WORM_REVS * 359.9 / ratio

    turn_times = np.linspace(t_turn_start, t_turn_end, turn_steps + 1).tolist()
    worm_values = np.linspace(0, -worm_total_deg, turn_steps + 1).tolist()
    wheel_values = np.linspace(0, -wheel_total_deg, turn_steps + 1).tolist()

    # Peg head and peg hardware rotate together (rx)
    for part_key in ("peg_head_1", "peg_washer_1", "peg_screw_1"):
        if part_key in children:
            animation.add_track(f"/assembly/{part_key}", "rx", turn_times, worm_values)

    # Wheel and string post rotate together (rz)
    for part_key in ("wheel_1", "string_post_1"):
        if part_key in children:
            animation.add_track(f"/assembly/{part_key}", "rz", turn_times, wheel_values)

    print(f"Animation: {duration}s (assembly + {WORM_REVS} worm revs)")
    print(f"Gear ratio: {ratio}:1")
    print("Sending to OCP viewer...")

    animation.animate(speed=1)

    if args.gif:
        print(f"Saving GIF to {args.gif} at {args.fps} fps...")
        animation.save_as_gif(args.gif, fps=args.fps)
        print(f"GIF saved: {args.gif}")

    print("Animation started. Use OCP viewer controls to replay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
