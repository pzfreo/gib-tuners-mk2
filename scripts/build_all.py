#!/usr/bin/env python3
"""Main CLI for building tuner assemblies.

Usage:
    python scripts/build_all.py --scale 1.0 --hand both
    python scripts/build_all.py --scale 2.0 --tolerance prototype_fdm
    python scripts/build_all.py --hand right --output-dir ./my_output
"""

import argparse
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
from gib_tuners.config.tolerances import TOLERANCE_PROFILES
from gib_tuners.assembly.gang_assembly import create_gang_assembly
from gib_tuners.export.step_export import export_assembly_step
from gib_tuners.utils.mirror import create_left_hand_config
from gib_tuners.utils.validation import validate_geometry


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Build parametric tuner assemblies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Production scale, both hands
    python scripts/build_all.py --scale 1.0 --hand both

    # 2x prototype for FDM printing
    python scripts/build_all.py --scale 2.0 --tolerance prototype_fdm

    # Just right-hand at production tolerance
    python scripts/build_all.py --hand right
        """,
    )

    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Geometry scale factor (default: 1.0)",
    )

    parser.add_argument(
        "--tolerance",
        choices=list(TOLERANCE_PROFILES.keys()),
        default="production",
        help="Tolerance profile (default: production)",
    )

    parser.add_argument(
        "--hand",
        choices=["right", "left", "both"],
        default="both",
        help="Which hand variant to build (default: both)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory (default: output/)",
    )

    parser.add_argument(
        "--gear-json",
        type=Path,
        default=Path("7mm-globoid.json"),
        help="Path to gear parameters JSON (default: 7mm-globoid.json)",
    )

    parser.add_argument(
        "--wheel-step",
        type=Path,
        default=Path("reference/wheel_m0.5_z12.step"),
        help="Path to wheel STEP file (default: reference/wheel_m0.5_z12.step)",
    )

    parser.add_argument(
        "--no-hardware",
        action="store_true",
        help="Exclude washers, screws, and E-clips from assembly",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only run validation, don't generate geometry",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Determine gear JSON path
    gear_json_path = args.gear_json
    if not gear_json_path.exists():
        print(f"Warning: Gear JSON not found at {gear_json_path}, using defaults")
        gear_json_path = None

    # Create base configuration (right-hand)
    rh_config = create_default_config(
        scale=args.scale,
        tolerance=args.tolerance,
        hand=Hand.RIGHT,
        gear_json_path=gear_json_path,
    )

    # Validate
    print("Validating geometry...")
    validation = validate_geometry(rh_config)
    print(validation)

    if not validation.passed:
        print("\nValidation failed! Fix issues before building.")
        return 1

    if args.validate_only:
        print("\nValidation passed.")
        return 0

    # Determine which hands to build
    hands_to_build = []
    if args.hand in ("right", "both"):
        hands_to_build.append(("rh", rh_config))
    if args.hand in ("left", "both"):
        lh_config = create_left_hand_config(rh_config)
        hands_to_build.append(("lh", lh_config))

    # Build and export
    wheel_step = args.wheel_step if args.wheel_step.exists() else None
    if wheel_step is None:
        print(f"Warning: Wheel STEP not found at {args.wheel_step}, using placeholder")

    for prefix, config in hands_to_build:
        print(f"\nBuilding {prefix.upper()} assembly...")

        output_dir = args.output_dir / prefix
        output_dir.mkdir(parents=True, exist_ok=True)

        assembly = create_gang_assembly(
            config,
            wheel_step_path=wheel_step,
            include_hardware=not args.no_hardware,
        )

        print(f"Exporting to {output_dir}...")
        exported = export_assembly_step(assembly, output_dir, prefix=f"{prefix}_")

        if args.verbose:
            print("Exported files:")
            for name, path in exported.items():
                print(f"  {name}: {path}")

    print("\nBuild complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
