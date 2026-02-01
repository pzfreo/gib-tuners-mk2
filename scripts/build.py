#!/usr/bin/env python3
"""Build tuner components as STL and STEP files.

Exports individual components (frame, string_post, peg_head, wheel) with
left-hand variants created by mirroring the right-hand geometry.

Runs interference check before exporting (use --no-interference to skip).

Usage:
    # Build all at 2x scale (both hands, both formats)
    python scripts/build.py --gear balanced --scale 2.0

    # Build RH only, 3-gang frame
    python scripts/build.py --gear balanced --hand right --num-housings 3

    # STL only
    python scripts/build.py --gear balanced --format stl

    # STEP only for CAD work
    python scripts/build.py --gear balanced --format step

    # Skip interference check
    python scripts/build.py --gear balanced --no-interference
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.config.parameters import Hand, WormZMode
from gib_tuners.config.tolerances import TOLERANCE_PROFILES
from gib_tuners.components.frame import create_frame
from gib_tuners.components.peg_head import create_peg_head
from gib_tuners.components.string_post import create_string_post
from gib_tuners.components.wheel import load_wheel, create_wheel_placeholder
from gib_tuners.assembly.gang_assembly import create_positioned_assembly, run_interference_report
from gib_tuners.export.stl_export import export_stl
from gib_tuners.export.step_export import export_step
from gib_tuners.utils.mirror import mirror_for_left_hand

REFERENCE_DIR = Path(__file__).parent.parent / "reference"

# Available components (no hardware)
COMPONENTS = ["frame", "string_post", "peg_head", "wheel"]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Build tuner components as STL and STEP files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Build all at 2x scale (both hands, both formats)
    python scripts/build.py --scale 2.0

    # Build RH only, 3-gang frame
    python scripts/build.py --hand right --num-housings 3

    # STL only
    python scripts/build.py --format stl

    # STEP only for CAD work
    python scripts/build.py --format step

    # Single housing for fit testing
    python scripts/build.py --scale 2.0 --num-housings 1
        """,
    )

    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Geometry scale factor (default: 1.0, use 2.0 for FDM prototypes)",
    )

    parser.add_argument(
        "--tolerance",
        choices=list(TOLERANCE_PROFILES.keys()),
        default="production",
        help="Tolerance profile (default: production, use prototype_fdm for FDM)",
    )

    parser.add_argument(
        "--hand",
        choices=["right", "left", "both"],
        default="both",
        help="Which hand variant to build (default: both)",
    )

    parser.add_argument(
        "--format",
        choices=["stl", "step", "both"],
        default="stl",
        help="Output format (default: stl - STEP may have non-manifold edges)",
    )

    parser.add_argument(
        "--num-housings",
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=5,
        help="Number of housings for frame (default: 5)",
    )

    parser.add_argument(
        "--components",
        nargs="+",
        choices=COMPONENTS + ["all"],
        default=["all"],
        help="Components to build (default: all)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory (default: output/)",
    )

    parser.add_argument(
        "--wheel-step",
        type=Path,
        default=REFERENCE_DIR / "wheel_m0.5_z13.step",
        help="Path to wheel STEP file",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    parser.add_argument(
        "--no-interference",
        action="store_true",
        help="Skip interference check",
    )

    parser.add_argument(
        "--gear",
        type=str,
        required=True,
        help="Gear config name (e.g., 'balanced'). Use --list-gears to see options.",
    )

    parser.add_argument(
        "--list-gears",
        action="store_true",
        help="List available gear configurations and exit",
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


def export_stl_quality(shape, path: Path, linear_tol: float = 0.01, angular_tol: float = 0.5):
    """Export STL with explicit tessellation and mesh repair.

    Uses BRepMesh_IncrementalMesh with moderate tolerances (0.01mm linear)
    to avoid non-manifold edges from null triangulation on thin faces.
    Repairs small holes if any remain.
    """
    import tempfile
    from OCP.StlAPI import StlAPI_Writer
    from OCP.BRepMesh import BRepMesh_IncrementalMesh

    wrapped = shape.wrapped if hasattr(shape, 'wrapped') else shape
    mesh_algo = BRepMesh_IncrementalMesh(wrapped, linear_tol, False, angular_tol, True)
    mesh_algo.Perform()

    # Export to temp file first
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
        temp_path = f.name

    writer = StlAPI_Writer()
    writer.Write(wrapped, temp_path)

    # Repair small holes using trimesh
    try:
        import trimesh
        import numpy as np
        from collections import defaultdict

        mesh = trimesh.load(temp_path)

        # Find boundary edges (holes)
        edge_to_faces = defaultdict(list)
        for fi, face in enumerate(mesh.faces):
            for i in range(3):
                edge = tuple(sorted([face[i], face[(i + 1) % 3]]))
                edge_to_faces[edge].append(fi)

        boundary_edges = [e for e, faces in edge_to_faces.items() if len(faces) == 1]

        if boundary_edges and len(boundary_edges) <= 10:
            # Build ordered boundary loop and fan triangulate to close hole
            edges_set = set(boundary_edges)
            loop = list(boundary_edges[0])
            edges_set.remove(boundary_edges[0])

            while edges_set:
                last = loop[-1]
                found = False
                for e in list(edges_set):
                    if last in e:
                        next_v = e[0] if e[1] == last else e[1]
                        if next_v != loop[0]:
                            loop.append(next_v)
                        edges_set.remove(e)
                        found = True
                        break
                if not found:
                    break

            if len(loop) >= 3:
                new_faces = [[loop[0], loop[i], loop[i + 1]] for i in range(1, len(loop) - 1)]
                all_faces = np.vstack([mesh.faces, np.array(new_faces)])
                mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=all_faces)
                mesh.fix_normals()

        mesh.export(str(path))
    except ImportError:
        # trimesh not available, use raw export
        import shutil
        shutil.move(temp_path, str(path))
    finally:
        import os
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def export_component(shape, output_dir: Path, basename: str, fmt: str) -> list[Path]:
    """Export a component in the specified format(s).

    Args:
        shape: Part or Compound to export
        output_dir: Output directory
        basename: Base filename (without extension)
        fmt: Format - "stl", "step", or "both"

    Returns:
        List of exported file paths
    """
    exported = []

    if fmt in ("stl", "both"):
        stl_path = output_dir / f"{basename}.stl"
        try:
            export_stl_quality(shape, stl_path)
            exported.append(stl_path)
            print(f"  -> {stl_path}")
        except Exception as e:
            print(f"  STL export failed for {basename}: {e}")

    if fmt in ("step", "both"):
        step_path = output_dir / f"{basename}.step"
        try:
            export_step(shape, step_path)
            exported.append(step_path)
            print(f"  -> {step_path}")
        except Exception as e:
            print(f"  STEP export failed for {basename}: {e}")

    return exported


def main() -> int:
    """Main entry point."""
    # Handle --list-gears before argparse requires --gear
    if "--list-gears" in sys.argv:
        from gib_tuners.config.defaults import list_gear_configs
        configs = list_gear_configs()
        print("Available gear configs:", ", ".join(configs) if configs else "(none)")
        return 0

    args = parse_args()

    # Determine which components to build
    if "all" in args.components:
        components_to_build = COMPONENTS
    else:
        components_to_build = args.components

    # Determine which hands to build
    build_rh = args.hand in ("right", "both")
    build_lh = args.hand in ("left", "both")

    # Resolve gear config paths
    gear_paths = resolve_gear_config(args.gear)

    # Create RH configuration (always needed as base)
    config = create_default_config(
        scale=args.scale,
        tolerance=args.tolerance,
        hand=Hand.RIGHT,
        gear_json_path=gear_paths.json_path,
        config_dir=gear_paths.config_dir,
    )

    # Determine worm Z mode from CLI flags
    if args.force_centered_worm:
        worm_z_mode = WormZMode.CENTERED
    elif args.force_aligned_worm:
        worm_z_mode = WormZMode.ALIGNED
    else:
        worm_z_mode = config.gear.worm_z_mode  # AUTO (from JSON hints)

    # Adjust num_housings for frame and worm_z_mode
    config = replace(
        config,
        frame=replace(config.frame, num_housings=args.num_housings),
        gear=replace(config.gear, worm_z_mode=worm_z_mode),
    )

    # Create output directory (subdirectory per gear config)
    output_dir = args.output_dir / args.gear
    output_dir.mkdir(parents=True, exist_ok=True)

    gear_label = args.gear
    print(f"Building components at {args.scale}x scale, {args.tolerance} tolerance")
    print(f"Gear config: {gear_label}")
    print(f"Hands: {args.hand}, Format: {args.format}")
    print(f"Output directory: {output_dir}")
    print()

    # Run interference check before exporting
    if not args.no_interference:
        print("Checking for interference...")
        interference_failed = False

        if build_rh:
            rh_assembly = create_positioned_assembly(
                config,
                wheel_step_path=gear_paths.wheel_step,
                worm_step_path=gear_paths.worm_step,
            )
            print("RH Interference:")
            if not run_interference_report(rh_assembly):
                interference_failed = True

        if build_lh:
            lh_config = replace(config, hand=Hand.LEFT)
            lh_assembly = create_positioned_assembly(
                lh_config,
                wheel_step_path=gear_paths.wheel_step,
                worm_step_path=gear_paths.worm_step,
            )
            print("LH Interference:")
            if not run_interference_report(lh_assembly):
                interference_failed = True

        if interference_failed:
            print("\nWARNING: Interference detected! Components may not fit correctly.")
            print("Continuing with export anyway...\n")
        else:
            print()

    exported = []

    # Build frame (L/R dependent - mirror RH for LH)
    if "frame" in components_to_build:
        print(f"Building frame ({args.num_housings}-gang)...")
        rh_frame = create_frame(config)

        if build_rh:
            basename = f"frame_rh_{args.num_housings}gang"
            exported.extend(export_component(rh_frame, output_dir, basename, args.format))

        if build_lh:
            lh_config = replace(config, hand=Hand.LEFT)
            lh_frame = create_frame(lh_config)
            basename = f"frame_lh_{args.num_housings}gang"
            exported.extend(export_component(lh_frame, output_dir, basename, args.format))

    # Build string post (symmetric - same for both hands)
    if "string_post" in components_to_build:
        print("Building string post...")
        string_post = create_string_post(config)
        basename = "string_post"
        exported.extend(export_component(string_post, output_dir, basename, args.format))

    # Build peg head (L/R dependent - mirror RH for LH due to worm helix)
    if "peg_head" in components_to_build:
        print("Building peg head...")
        try:
            rh_peg_head = create_peg_head(
                config,
                worm_step_path=gear_paths.worm_step,
                worm_length=config.gear.worm.length,
            )

            if build_rh:
                basename = "peg_head_rh"
                exported.extend(export_component(rh_peg_head, output_dir, basename, args.format))

            if build_lh:
                lh_peg_head = mirror_for_left_hand(rh_peg_head)
                basename = "peg_head_lh"
                exported.extend(export_component(lh_peg_head, output_dir, basename, args.format))

        except FileNotFoundError as e:
            print(f"  Skipping peg_head: {e}")

    # Build wheel (L/R dependent - mirror RH for LH due to helix direction)
    if "wheel" in components_to_build:
        print("Building wheel...")
        try:
            # Use gear config wheel STEP if available, else CLI arg fallback
            wheel_step = gear_paths.wheel_step or args.wheel_step
            if wheel_step and wheel_step.exists():
                rh_wheel = load_wheel(wheel_step)
                if args.scale != 1.0:
                    rh_wheel = rh_wheel.scale(args.scale)
            else:
                print("  Warning: wheel STEP not found, using placeholder")
                rh_wheel = create_wheel_placeholder(config)

            if build_rh:
                basename = "wheel_rh"
                exported.extend(export_component(rh_wheel, output_dir, basename, args.format))

            if build_lh:
                lh_wheel = mirror_for_left_hand(rh_wheel)
                basename = "wheel_lh"
                exported.extend(export_component(lh_wheel, output_dir, basename, args.format))

        except Exception as e:
            print(f"  Warning: Failed to build wheel: {e}")

    print()
    print(f"Exported {len(exported)} files to {output_dir}")

    if args.verbose:
        print("\nPrint settings suggestions for FDM:")
        print("  - Frame: 0.2mm layer height, 20% infill, supports on build plate")
        print("  - String post: 0.1mm layer height, 100% infill, print vertically")
        print("  - Peg head: 0.15mm layer height, 40% infill")
        print("  - Wheel: 0.1mm layer height, 100% infill for tooth strength")

    return 0


if __name__ == "__main__":
    sys.exit(main())
