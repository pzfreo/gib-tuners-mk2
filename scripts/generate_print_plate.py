#!/usr/bin/env python3
"""Generate build plates for tuner assemblies (FDM or Resin).

Supports two printing processes with optimized orientations:

FDM (Fused Deposition Modeling):
- Frames: Flat on mounting face to minimize supports
- Shafts: Horizontal for maximum bending/shear strength
- Wheels: Flat for accuracy
- Default plate: 256x256mm (Bambu P1S)

Resin (SLA/DLP):
- Parts tilted 30-45° to reduce peel forces and suction
- Smaller cross-section per layer for better success
- Default plate: 200x125mm (medium format resin)

Usage:
    python scripts/generate_print_plate.py --hand right --num-housings 1
    python scripts/generate_print_plate.py --process resin --scale 1.0
    python scripts/generate_print_plate.py --scale 2.0 --output prototype_plate.3mf
"""

import argparse
import sys
import tempfile
from pathlib import Path
from dataclasses import replace, dataclass
import math

import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import trimesh
    from trimesh.transformations import rotation_matrix, translation_matrix
except ImportError:
    print("Error: trimesh is required. Install with: pip install trimesh[easy]")
    sys.exit(1)

from build123d import export_stl, Shape, Location, Axis, Box
from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
from gib_tuners.components.frame import create_frame
from gib_tuners.components.peg_head import create_peg_head
from gib_tuners.components.string_post import create_string_post
from gib_tuners.components.wheel import load_wheel, create_wheel_placeholder
from gib_tuners.utils.mirror import mirror_for_left_hand

# Plate sizes for different printers
PLATE_SIZES = {
    "fdm": (256, 256),       # Bambu P1S / Prusa MK3
    "fdm_small": (180, 180), # Smaller FDM printers
    "resin": (200, 125),     # Medium format resin (Saturn, Mars Pro)
    "resin_small": (120, 68), # Small format resin (Mars, Photon)
}

# Padding between parts
PADDING = {
    "fdm": 5.0,
    "resin": 3.0,  # Resin can pack tighter
}

# Resin tilt angle (degrees)
RESIN_TILT_ANGLE = 35.0


@dataclass
class Packable:
    name: str
    mesh: trimesh.Trimesh
    shape: Shape

    def copy(self):
        return Packable(self.name, self.mesh.copy(), self.shape)

    def translate(self, x, y, z):
        matrix = translation_matrix([x, y, z])
        self.mesh.apply_transform(matrix)
        self.shape = self.shape.moved(Location((x, y, z)))

    def rotate(self, angle_deg, axis_vec):
        matrix = rotation_matrix(math.radians(angle_deg), axis_vec)
        self.mesh.apply_transform(matrix)
        self.shape = self.shape.rotate(Axis((0, 0, 0), tuple(axis_vec)), angle_deg)

    def center_xy_drop_z(self):
        """Move to Z=0 and center XY."""
        bounds = self.mesh.bounds
        min_x, min_y, min_z = bounds[0]
        max_x, max_y, max_z = bounds[1]

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        self.translate(-center_x, -center_y, -min_z)


def b3d_to_trimesh(shape, name="part"):
    """Convert a build123d shape to a trimesh object via temporary STL."""
    with tempfile.NamedTemporaryFile(suffix=".stl") as tmp:
        export_stl(shape, tmp.name)
        mesh = trimesh.load(tmp.name, file_type="stl")
    mesh.metadata["name"] = name
    return mesh


# =============================================================================
# FDM Orientation Functions
# =============================================================================

def orient_frame_fdm(p: Packable):
    """FDM: Frame with mounting plate facing DOWN (flat on bed)."""
    p.rotate(180, [1, 0, 0])
    p.center_xy_drop_z()


def orient_wheel_fdm(p: Packable):
    """FDM: Wheel flat on bed for accuracy."""
    p.center_xy_drop_z()


def orient_peg_fdm(p: Packable):
    """FDM: Peg head horizontal for shaft strength."""
    # Peg is already oriented with shaft along X after creation
    p.center_xy_drop_z()


def orient_post_fdm(p: Packable):
    """FDM: String post horizontal for shaft strength."""
    # Post shaft is along Z, rotate to lie flat
    p.rotate(90, [0, 1, 0])
    p.center_xy_drop_z()


# =============================================================================
# Resin Orientation Functions
# =============================================================================

def orient_frame_resin(p: Packable):
    """Resin: Frame tilted for reduced peel force."""
    # Tilt around X axis so layers build at an angle
    p.rotate(RESIN_TILT_ANGLE, [1, 0, 0])
    p.center_xy_drop_z()


def orient_wheel_resin(p: Packable):
    """Resin: Wheel tilted to reduce suction on large flat faces."""
    p.rotate(RESIN_TILT_ANGLE, [1, 0, 0])
    p.center_xy_drop_z()


def orient_peg_resin(p: Packable):
    """Resin: Peg tilted for better layer adhesion on worm threads."""
    # Tilt slightly for better thread printing
    p.rotate(RESIN_TILT_ANGLE, [0, 1, 0])
    p.center_xy_drop_z()


def orient_post_resin(p: Packable):
    """Resin: String post vertical (small cross-section per layer)."""
    # Post can print vertically on resin - small diameter = low suction
    p.center_xy_drop_z()


def pack_packables(packables, plate_size, padding):
    """Simple 2D bin packing."""
    current_x = -plate_size[0] / 2 + padding
    current_y = -plate_size[1] / 2 + padding
    max_row_y = 0.0

    # Sort by bounding box area (largest first)
    packables.sort(key=lambda p: p.mesh.extents[0] * p.mesh.extents[1], reverse=True)

    for p in packables:
        width = p.mesh.extents[0]
        depth = p.mesh.extents[1]

        # Check if we need a new row
        if current_x + width > plate_size[0] / 2 - padding:
            current_x = -plate_size[0] / 2 + padding
            current_y += max_row_y + padding
            max_row_y = 0.0

        bounds = p.mesh.bounds
        min_x = bounds[0][0]
        min_y = bounds[0][1]

        shift_x = current_x - min_x
        shift_y = current_y - min_y

        p.translate(shift_x, shift_y, 0)

        current_x += width + padding
        max_row_y = max(max_row_y, depth)

    return packables


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate build plate for tuners (FDM or Resin)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # FDM printing (default)
    python scripts/generate_print_plate.py --num-housings 1

    # Resin printing
    python scripts/generate_print_plate.py --process resin

    # 2x scale prototype for FDM
    python scripts/generate_print_plate.py --scale 2.0 --process fdm

    # Visualize before export
    python scripts/generate_print_plate.py --viz
        """,
    )
    parser.add_argument(
        "--process",
        choices=["fdm", "resin"],
        default="fdm",
        help="Printing process (default: fdm)",
    )
    parser.add_argument(
        "--hand",
        choices=["right", "left"],
        default="right",
        help="Hand variant (default: right)",
    )
    parser.add_argument(
        "--num-housings",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help="Number of gangs (default: 1)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Scale factor (default: 1.0, use 2.0 for prototypes)",
    )
    parser.add_argument(
        "--plate-size",
        choices=list(PLATE_SIZES.keys()),
        default=None,
        help="Override plate size (default: based on process)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output filename (default: tuner_{process}_{hand}.3mf)",
    )
    parser.add_argument(
        "--wheel-step",
        type=Path,
        default=Path("reference/wheel_m0.5_z13.step"),
        help="Wheel STEP file",
    )
    parser.add_argument(
        "--viz",
        action="store_true",
        help="Visualize the build plate",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Determine plate size and padding
    plate_key = args.plate_size or args.process
    plate_size = PLATE_SIZES.get(plate_key, PLATE_SIZES[args.process])
    padding = PADDING.get(args.process, 5.0)

    # Default output filename
    if args.output is None:
        args.output = f"tuner_{args.process}_{args.hand}.3mf"

    # Select orientation functions based on process
    if args.process == "fdm":
        orient_frame = orient_frame_fdm
        orient_wheel = orient_wheel_fdm
        orient_peg = orient_peg_fdm
        orient_post = orient_post_fdm
    else:  # resin
        orient_frame = orient_frame_resin
        orient_wheel = orient_wheel_resin
        orient_peg = orient_peg_resin
        orient_post = orient_post_resin

    # Configuration
    hand_enum = Hand.RIGHT if args.hand == "right" else Hand.LEFT
    config = create_default_config(scale=args.scale, hand=hand_enum)
    config = replace(config, frame=replace(config.frame, num_housings=args.num_housings))

    print(f"=== Build Plate Generator ===")
    print(f"Process: {args.process.upper()}")
    print(f"Plate size: {plate_size[0]}x{plate_size[1]}mm")
    print(f"Config: {args.num_housings}-gang {args.hand.upper()} @ {args.scale}x scale")
    print()

    packables = []

    # Generate Frame (config already has correct hand, no mirroring needed)
    print("Generating Frame...")
    frame_shape = create_frame(config)

    frame_mesh = b3d_to_trimesh(frame_shape, "Frame")
    p_frame = Packable("Frame", frame_mesh, frame_shape)
    orient_frame(p_frame)
    packables.append(p_frame)

    # Generate Components
    print(f"Generating {args.num_housings} sets of components...")

    # Wheel
    if args.wheel_step.exists():
        wheel_shape = load_wheel(args.wheel_step)
        if args.scale != 1.0:
            wheel_shape = wheel_shape.scale(args.scale)
    else:
        print("  Using placeholder wheel")
        wheel_shape = create_wheel_placeholder(config)

    if args.hand == "left":
        wheel_shape = mirror_for_left_hand(wheel_shape)

    # Peg Head (Worm)
    peg_shape = create_peg_head(config)
    if args.hand == "left":
        peg_shape = mirror_for_left_hand(peg_shape)

    # String Post
    post_shape = create_string_post(config)

    # Create base packables with process-specific orientations
    p_wheel = Packable("Wheel", b3d_to_trimesh(wheel_shape, "Wheel"), wheel_shape)
    orient_wheel(p_wheel)

    p_peg = Packable("PegHead", b3d_to_trimesh(peg_shape, "PegHead"), peg_shape)
    orient_peg(p_peg)

    p_post = Packable("StringPost", b3d_to_trimesh(post_shape, "StringPost"), post_shape)
    orient_post(p_post)

    for i in range(args.num_housings):
        packables.append(p_wheel.copy())
        packables.append(p_peg.copy())
        packables.append(p_post.copy())

    # Pack
    print("Packing build plate...")
    packed = pack_packables(packables, plate_size, padding)

    # Check if everything fits
    max_y = max(p.mesh.bounds[1][1] for p in packed)
    if max_y > plate_size[1] / 2:
        print(f"  Warning: Parts extend beyond plate ({max_y:.1f}mm > {plate_size[1]/2:.1f}mm)")
        print("  Consider using a larger plate or fewer housings")

    # Export
    scene_meshes = [p.mesh for p in packed]
    for p in packed:
        p.mesh.metadata["name"] = p.name

    scene = trimesh.Scene(scene_meshes)
    output_path = Path(args.output)

    print(f"Exporting to {output_path}...")
    scene.export(output_path)
    print(f"Done. {len(packed)} parts packed.")

    # Print summary
    print()
    print(f"=== Printing Notes ({args.process.upper()}) ===")
    if args.process == "fdm":
        print("- Frame: Print flat, minimal supports needed")
        print("- Posts: Horizontal orientation for shaft strength")
        print("- Wheels: Flat for dimensional accuracy")
        print("- Suggested: 0.2mm layer height, 20% infill")
    else:
        print(f"- Parts tilted {RESIN_TILT_ANGLE}° to reduce peel forces")
        print("- Add supports to tilted faces")
        print("- Posts: Vertical (small cross-section per layer)")
        print("- Suggested: 0.05mm layer height for fine detail")

    # Visualize
    if args.viz:
        print()
        print(f"Visualizing build plate with {len(packed)} items...")
        try:
            from ocp_vscode import show, Camera

            colors = {
                "Frame": (0.7, 0.7, 0.7),
                "Wheel": (0.8, 0.6, 0.2),
                "PegHead": (0.8, 0.6, 0.2),
                "StringPost": (0.8, 0.8, 0.8),
            }

            shapes = []
            names = []
            cols = []

            for i, p in enumerate(packed):
                shapes.append(p.shape)
                names.append(f"{p.name}_{i}")
                cols.append(colors.get(p.name, (0.5, 0.5, 0.5)))

            # Ghost build plate
            plate_ghost = Box(plate_size[0], plate_size[1], 1)
            plate_ghost = plate_ghost.moved(Location((0, 0, -0.5)))

            shapes.append(plate_ghost)
            names.append("BuildPlate")
            cols.append((0.1, 0.1, 0.1, 0.2))

            show(*shapes, names=names, colors=cols, reset_camera=Camera.RESET)

        except Exception as e:
            print(f"ocp_vscode failed: {e}")
            print("Using trimesh native viewer...")
            scene.show()


if __name__ == "__main__":
    main()
