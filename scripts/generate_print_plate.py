#!/usr/bin/env python3
"""Generate a Bambu P1S compatible 3MF build plate for tuner assemblies.

This script uses trimesh to pack and orient components for optimal strength:
- Frames: Flat on the mounting face (Z=0) to minimize supports and maximize stability.
- Worms/Pegs: Horizontal orientation for maximum shaft and tooth shear strength.
- String Posts: Horizontal orientation for maximum shaft bending strength.
- Wheels: Flat for accuracy and strength.

Usage:
    python scripts/generate_print_plate.py --hand right --num-housings 1
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

# Bambu P1S Build Volume (approximate safe area)
PLATE_SIZE = (256, 256)
PADDING = 5.0  # mm spacing between parts


@dataclass
class Packable:
    name: str
    mesh: trimesh.Trimesh
    shape: Shape

    def copy(self):
        # build123d Shape operations return new instances, so simple reference is fine
        # until we modify it (which creates a new one).
        # trimesh copy is needed because it mutates in place.
        return Packable(self.name, self.mesh.copy(), self.shape)

    def translate(self, x, y, z):
        # Trimesh
        matrix = translation_matrix([x, y, z])
        self.mesh.apply_transform(matrix)
        # build123d
        self.shape = self.shape.moved(Location((x, y, z)))

    def rotate(self, angle_deg, axis_vec):
        # Trimesh (radians)
        matrix = rotation_matrix(math.radians(angle_deg), axis_vec)
        self.mesh.apply_transform(matrix)
        # build123d (degrees, Axis)
        self.shape = self.shape.rotate(Axis((0,0,0), tuple(axis_vec)), angle_deg)
        
    def center_xy_drop_z(self):
        """Move to Z=0 and center XY."""
        bounds = self.mesh.bounds
        min_x, min_y, min_z = bounds[0]
        max_x, max_y, max_z = bounds[1]
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Translate so center is at 0,0 and min_z is at 0
        dx = -center_x
        dy = -center_y
        dz = -min_z
        
        self.translate(dx, dy, dz)


def b3d_to_trimesh(shape, name="part"):
    """Convert a build123d shape to a trimesh object via temporary STL."""
    with tempfile.NamedTemporaryFile(suffix=".stl") as tmp:
        export_stl(shape, tmp.name)
        mesh = trimesh.load(tmp.name, file_type="stl")
    mesh.metadata["name"] = name
    return mesh


def orient_frame(p: Packable):
    """Orient frame with mounting plate (Z=0) facing DOWN on the bed."""
    # Rotate 180 deg around X axis
    p.rotate(180, [1, 0, 0])
    p.center_xy_drop_z()


def orient_horizontal_shaft(p: Packable, axis='z'):
    """Orient a part that has its main shaft along 'axis' to be horizontal (along X)."""
    if axis == 'z':
        # Rotate 90 deg around Y
        p.rotate(90, [0, 1, 0])
    p.center_xy_drop_z()


def pack_packables(packables, plate_size):
    """Simple 2D bin packing."""
    current_x = -plate_size[0] / 2 + PADDING
    current_y = -plate_size[1] / 2 + PADDING
    max_row_y = 0.0
    
    # Sort by bounding box area (largest first)
    packables.sort(key=lambda p: p.mesh.extents[0] * p.mesh.extents[1], reverse=True)
    
    for p in packables:
        width = p.mesh.extents[0]
        depth = p.mesh.extents[1]
        
        # Check if we need a new row
        if current_x + width > plate_size[0] / 2 - PADDING:
            current_x = -plate_size[0] / 2 + PADDING
            current_y += max_row_y + PADDING
            max_row_y = 0.0
            
        bounds = p.mesh.bounds
        min_x = bounds[0][0]
        min_y = bounds[0][1]
        
        shift_x = current_x - min_x
        shift_y = current_y - min_y
        
        p.translate(shift_x, shift_y, 0)
        
        current_x += width + PADDING
        max_row_y = max(max_row_y, depth)
        
    return packables


def parse_args():
    parser = argparse.ArgumentParser(description="Generate 3MF build plate for tuners")
    parser.add_argument("--hand", choices=["right", "left"], default="right", help="Hand variant")
    parser.add_argument("--num-housings", type=int, default=1, choices=[1, 2, 3, 4, 5], help="Number of gangs")
    parser.add_argument("--scale", type=float, default=1.0, help="Scale factor (2.0 for prototypes)")
    parser.add_argument("--output", default="tuner_build_plate.3mf", help="Output filename")
    parser.add_argument("--wheel-step", type=Path, default=Path("reference/wheel_m0.5_z13.step"), help="Wheel STEP file")
    parser.add_argument("--viz", action="store_true", help="Visualize the build plate")
    return parser.parse_args()


def main():
    args = parse_args()
    
    # 1. Configuration
    hand_enum = Hand.RIGHT if args.hand == "right" else Hand.LEFT
    config = create_default_config(scale=args.scale, hand=hand_enum)
    config = replace(config, frame=replace(config.frame, num_housings=args.num_housings))
    
    print(f"Generating build plate for {args.num_housings}-gang {args.hand.upper()} tuner (Scale: {args.scale}x)")
    
    packables = []
    
    # 2. Generate Frame
    print("Generating Frame...")
    frame_shape = create_frame(config)
    if args.hand == "left":
        frame_shape = mirror_for_left_hand(frame_shape)
    
    frame_mesh = b3d_to_trimesh(frame_shape, "Frame")
    p_frame = Packable("Frame", frame_mesh, frame_shape)
    orient_frame(p_frame)
    packables.append(p_frame)
    
    # 3. Generate Components (n times)
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
    
    # Create base packables
    p_wheel = Packable("Wheel", b3d_to_trimesh(wheel_shape, "Wheel"), wheel_shape)
    p_wheel.center_xy_drop_z()
    
    p_peg = Packable("PegHead", b3d_to_trimesh(peg_shape, "PegHead"), peg_shape)
    p_peg.center_xy_drop_z()
    
    p_post = Packable("StringPost", b3d_to_trimesh(post_shape, "StringPost"), post_shape)
    orient_horizontal_shaft(p_post, axis='z')

    for i in range(args.num_housings):
        packables.append(p_wheel.copy())
        packables.append(p_peg.copy())
        packables.append(p_post.copy())

    # 4. Pack
    print("Packing build plate...")
    packed = pack_packables(packables, PLATE_SIZE)
    
    # 5. Export
    scene_meshes = [p.mesh for p in packed]
    # Ensure names are set
    for p in packed:
        p.mesh.metadata["name"] = p.name

    scene = trimesh.Scene(scene_meshes)
    output_path = Path(args.output)
    
    print(f"Exporting to {output_path}...")
    scene.export(output_path)
    print("Done.")

    # 6. Visualize
    if args.viz:
        print(f"Visualizing build plate with {len(packed)} items...")
        try:
            from ocp_vscode import show, Camera
            
            # Send the build123d SHAPES to the viewer
            viz_objects = {}
            for i, p in enumerate(packed):
                name = f"{p.name}_{i}"
                viz_objects[name] = p.shape
            
            # Colors
            colors = {
                "Frame": (0.7, 0.7, 0.7), 
                "Wheel": (0.8, 0.6, 0.2), 
                "PegHead": (0.8, 0.6, 0.2),
                "StringPost": (0.8, 0.8, 0.8),
            }
            
            # Create parallel lists for show() if dictionary doesn't support colors well in all versions
            # But ocp_vscode 2.0+ supports dicts well.
            # To apply colors to a dict, we might need a separate colors dict or loop.
            
            # Let's try the *args approach with names and colors lists
            shapes = []
            names = []
            cols = []
            
            for i, p in enumerate(packed):
                shapes.append(p.shape)
                names.append(f"{p.name}_{i}")
                cols.append(colors.get(p.name, (0.5, 0.5, 0.5)))

            # Create ghost build plate
            plate_ghost = Box(PLATE_SIZE[0], PLATE_SIZE[1], 1)
            plate_ghost.location = Location((0, 0, -0.5))
            
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