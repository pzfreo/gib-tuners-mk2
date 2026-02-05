#!/usr/bin/env python3
"""Generate engineering drawings for tuner components using FreeCAD TechDraw.

Creates orthographic views with dimension annotations for manufacturing.
Uses FreeCAD's TechDraw workbench for proper engineering drawing output.

Falls back to build123d SVG/DXF if FreeCAD is not available.

Usage:
    # Generate frame drawing (PDF + FCStd)
    python scripts/drawings.py --gear balanced --component frame

    # Generate all component drawings
    python scripts/drawings.py --gear balanced --all

    # Specify hand variant
    python scripts/drawings.py --gear bh11-cd --component frame --hand right

    # Use build123d fallback (SVG/DXF only, no FreeCAD needed)
    python scripts/drawings.py --gear balanced --all --format svg

    # List available gear configurations
    python scripts/drawings.py --list-gears
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gib_tuners.config.defaults import create_default_config, resolve_gear_config, list_gear_configs
from gib_tuners.config.parameters import Hand

FREECAD_BIN = "/Applications/FreeCAD.app/Contents/MacOS/FreeCAD"
FREECAD_SCRIPT = Path(__file__).parent / "freecad_drawing.py"

COMPONENTS = ["frame", "string_post", "wheel", "peg_head"]

# Map component names to STEP file patterns
STEP_PATTERNS = {
    "frame": "frame_{hand}_{n}gang.step",
    "string_post": "string_post.step",
    "wheel": "wheel_{hand}.step",
    "peg_head": "peg_head_{hand}.step",
}


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate engineering drawings for tuner components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/drawings.py --gear balanced --component frame
    python scripts/drawings.py --gear bh11-cd --all
    python scripts/drawings.py --gear balanced --all --format svg
    python scripts/drawings.py --list-gears
        """,
    )

    parser.add_argument("--gear", type=str, help="Gear config name")
    parser.add_argument("--list-gears", action="store_true", help="List gear configs and exit")
    parser.add_argument("--component", choices=COMPONENTS, help="Component to draw")
    parser.add_argument("--all", action="store_true", help="Draw all components")
    parser.add_argument(
        "--format", choices=["pdf", "svg", "dxf"], default="pdf",
        help="Output format: pdf (FreeCAD), svg/dxf (build123d fallback)",
    )
    parser.add_argument("--hand", choices=["right", "left", "both"], default="right")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--output-dir", type=Path, default=Path("drawings"))
    parser.add_argument("--num-housings", type=int, choices=[1, 2, 3, 4, 5], default=5)

    return parser.parse_args()


def find_step_file(output_dir: Path, component: str, hand: str, num_housings: int) -> Path | None:
    """Find the STEP file for a component."""
    pattern = STEP_PATTERNS.get(component, "")
    hand_str = "rh" if hand == "right" else "lh"
    filename = pattern.format(hand=hand_str, n=num_housings)
    path = output_dir / filename
    if path.exists():
        return path
    return None


def generate_step_if_needed(gear: str, component: str, hand: str, num_housings: int, scale: float) -> Path | None:
    """Generate STEP file using build.py if it doesn't exist."""
    gear_paths = resolve_gear_config(gear)
    output_dir = Path("output") / gear

    step_path = find_step_file(output_dir, component, hand, num_housings)
    if step_path:
        return step_path

    # Generate it
    print(f"  Generating STEP file for {component}...")
    hand_flag = hand
    cmd = [
        sys.executable, "scripts/build.py",
        "--gear", gear,
        "--format", "step",
        "--hand", hand_flag,
        "--num-housings", str(num_housings),
        "--components", component,
        "--no-interference",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Build failed: {result.stderr}")
        return None

    return find_step_file(output_dir, component, hand, num_housings)


def run_freecad_drawing(step_file: Path, output_dir: Path, component: str, title: str, hand: str, gear: str = "") -> bool:
    """Run FreeCAD to generate engineering drawing.

    Returns True if successful.
    """
    if not Path(FREECAD_BIN).exists():
        print(f"  FreeCAD not found at {FREECAD_BIN}")
        return False

    hand_str = "rh" if hand == "right" else "lh"
    basename = f"{component}_{hand_str}" if hand_str else component

    # Clean up any previous status file
    status_path = output_dir / f".drawing_status_{basename}"
    if status_path.exists():
        status_path.unlink()

    env = os.environ.copy()
    env["DRAWING_STEP_FILE"] = str(step_file)
    env["DRAWING_OUTPUT_DIR"] = str(output_dir)
    env["DRAWING_COMPONENT"] = component
    env["DRAWING_TITLE"] = title
    env["DRAWING_HAND"] = hand_str
    env["DRAWING_GEAR"] = gear

    timed_out = False
    try:
        subprocess.run(
            [FREECAD_BIN, str(FREECAD_SCRIPT)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        timed_out = True

    # Check status file (FreeCAD may finish work before process exits)
    if status_path.exists():
        content = status_path.read_text()
        for line in content.strip().split("\n"):
            if "=" in line:
                key, val = line.split("=", 1)
                size = Path(val).stat().st_size if Path(val).exists() else 0
                print(f"  {key}: {val} ({size} bytes)")
        status_path.unlink()
        return "DONE" in content

    if timed_out:
        print(f"  FreeCAD timed out")
    else:
        print(f"  FreeCAD did not produce status file")
    return False


def run_build123d_drawing(gear: str, component: str, output_dir: Path, fmt: str, num_housings: int, scale: float):
    """Fallback: use build123d drawing export for SVG/DXF."""
    from dataclasses import replace
    from gib_tuners.export.drawing_export import (
        create_frame_drawing,
        create_string_post_drawing,
        create_wheel_drawing,
        create_peg_head_drawing,
    )

    gear_paths = resolve_gear_config(gear)
    config = create_default_config(
        scale=scale,
        hand=Hand.RIGHT,
        gear_json_path=gear_paths.json_path,
        config_dir=gear_paths.config_dir,
    )
    config = replace(config, frame=replace(config.frame, num_housings=num_housings))

    formats = [fmt]
    creators = {
        "frame": lambda: create_frame_drawing(config, output_dir, formats),
        "string_post": lambda: create_string_post_drawing(config, output_dir, formats),
        "wheel": lambda: create_wheel_drawing(config, output_dir, gear_paths.wheel_step, formats),
        "peg_head": lambda: create_peg_head_drawing(config, output_dir, gear_paths.worm_step, formats),
    }

    creator = creators.get(component)
    if creator:
        return creator()
    return []


def main() -> int:
    """Main entry point."""
    if "--list-gears" in sys.argv:
        configs = list_gear_configs()
        print("Available gear configs:", ", ".join(configs) if configs else "(none)")
        return 0

    args = parse_args()

    if not args.gear:
        print("Error: --gear is required. Use --list-gears to see options.")
        return 1
    if not args.component and not args.all:
        print("Error: specify --component <name> or --all")
        return 1

    try:
        resolve_gear_config(args.gear)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    output_dir = args.output_dir / args.gear
    output_dir.mkdir(parents=True, exist_ok=True)

    components = COMPONENTS if args.all else [args.component]
    hands = ["right", "left"] if args.hand == "both" else [args.hand]

    print(f"Generating engineering drawings")
    print(f"Gear: {args.gear}, Format: {args.format}, Hand: {args.hand}")
    print(f"Output: {output_dir}")
    print()

    total = 0

    for component in components:
        for hand in hands:
            hand_str = "rh" if hand == "right" else "lh"
            hand_label = "Right" if hand == "right" else "Left"
            title = f"Parametric {component.replace('_', ' ').title()} {hand_label}"

            # String post is symmetric
            if component == "string_post" and hand == "left":
                continue

            print(f"{component} ({hand_str})...")

            if args.format == "pdf":
                # FreeCAD path
                step_file = generate_step_if_needed(
                    args.gear, component, hand, args.num_housings, args.scale
                )
                if not step_file:
                    print(f"  Skipping: no STEP file")
                    continue

                if run_freecad_drawing(step_file, output_dir, component, title, hand, gear=args.gear):
                    total += 1
                else:
                    print(f"  FreeCAD drawing failed")
            else:
                # build123d fallback
                try:
                    exported = run_build123d_drawing(
                        args.gear, component, output_dir, args.format,
                        args.num_housings, args.scale,
                    )
                    for p in exported:
                        print(f"  -> {p}")
                    total += len(exported)
                except Exception as e:
                    print(f"  Error: {e}")

    print()
    print(f"Generated {total} drawing(s) in {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
