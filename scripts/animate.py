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
        "--export-blender",
        action="store_true",
        help="Export to Blender (GLB + Animation Script)",
    )
    return parser.parse_args()


def b3d_to_trimesh(shape, name="part", color=None):
    """Convert build123d shape to trimesh."""
    import trimesh
    import tempfile
    from build123d import export_stl
    
    with tempfile.NamedTemporaryFile(suffix=".stl") as tmp:
        export_stl(shape, tmp.name)
        mesh = trimesh.load(tmp.name, file_type="stl")
    
    mesh.metadata["name"] = name
    if color:
        # Simple color handling
        c = [int(x * 255) for x in color[:3]]
        if len(color) > 3:
            c.append(int(color[3] * 255))
        else:
            c.append(255)
        mesh.visual.face_colors = c
    return mesh


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

    wheel_pivot_loc = Location((0, translation_y, wheel_z))
    wheel_pivot_vec = (0, translation_y, wheel_z)

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
    peg_pivot_loc = Location((peg_x, peg_y, worm_z))
    peg_pivot_vec = (peg_x, peg_y, worm_z)

    print(f"  Wheel pivot: (0, {translation_y:.2f}, {wheel_z:.2f})")
    print(f"  Peg pivot: ({peg_x:.2f}, {peg_y:.2f}, {worm_z:.2f})")

    # Export Logic
    if args.export_blender:
        print("\nExporting to Blender...")
        try:
            import trimesh
            from trimesh.transformations import translation_matrix
        except ImportError:
            print("Error: trimesh is required. Install with: pip install trimesh[easy]")
            return 1

        # Groups define pivots
        # Everything else is static (frame)
        groups = {
            "peg_group": {
                "pivot": peg_pivot_vec,
                "parts": [peg_head, peg_washer, peg_screw],
                "names": ["peg_head", "peg_washer", "peg_screw"]
            },
            "wheel_group": {
                "pivot": wheel_pivot_vec,
                "parts": [wheel, string_post, wheel_washer, wheel_screw],
                "names": ["wheel", "string_post", "wheel_washer", "wheel_screw"]
            }
        }
        
        scene = trimesh.Scene()
        
        # 1. Export Static Parts (Frame)
        print("  Processing static parts...")
        frame_mesh = b3d_to_trimesh(frame, "frame", color=(0.5, 0.5, 0.5))
        scene.add_geometry(frame_mesh, node_name="frame", geom_name="frame_geo")
        
        # 2. Export Moving Parts (Re-centered)
        print("  Processing moving parts...")
        for grp_name, data in groups.items():
            pivot = data["pivot"]
            # Inverse translation to center geometry at origin
            center_loc = Location((-pivot[0], -pivot[1], -pivot[2]))
            
            for part, name in zip(data["parts"], data["names"]):
                if part is None: continue
                # Move part to local origin (centered on pivot)
                centered_part = part.moved(center_loc)
                mesh = b3d_to_trimesh(centered_part, name, color=(0.8, 0.6, 0.2))
                
                # Add to scene with transform placing it back at pivot
                # We append suffix to node name to make it easy to find
                scene.add_geometry(
                    mesh, 
                    node_name=name, 
                    geom_name=f"{name}_geo",
                    transform=translation_matrix(pivot)
                )

        glb_filename = "tuner_anim_model.glb"
        scene.export(glb_filename)
        print(f"  Saved model: {glb_filename}")

        # 3. Generate Blender Script
        # We need the animation data
        steps = args.steps
        duration = args.duration
        
        # Calculate tracks (same as below)
        worm_direction = -1 if config.hand == Hand.RIGHT else 1
        wheel_direction = -1 if config.hand == Hand.RIGHT else 1
        worm_total_deg = args.worm_revs * 359.9
        wheel_total_deg = args.worm_revs * 359.9 / ratio
        
        # Generate frames
        # Blender default is 24 fps
        fps = 24
        total_frames = int(duration * fps)
        
        worm_track = []
        wheel_track = []
        
        for i in range(total_frames + 1):
            t = i / total_frames
            w_angle = float(np.radians(t * worm_total_deg * worm_direction))
            wh_angle = float(np.radians(t * wheel_total_deg * wheel_direction))
            worm_track.append((i + 1, w_angle))
            wheel_track.append((i + 1, wh_angle))
            
        # Calculate absolute path to ensure Blender finds the file
        import os
        abs_glb_path = os.path.abspath(glb_filename).replace("\\", "/")

        script_content = f"""import bpy
import math

# Config
glb_path = "{abs_glb_path}"
fps = {fps}
total_frames = {total_frames}

# Animation Data (Frame, Angle in Radians)
# Peg Head: Rotate around X
worm_track = {worm_track}
peg_pivot = {list(peg_pivot_vec)}

# Wheel/Post: Rotate around Z
wheel_track = {wheel_track}
wheel_pivot = {list(wheel_pivot_vec)}

def create_and_animate_pivot(name, location, track, axis_index, child_names):
    # Create Empty object directly in data
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.location = location
    
    # Link to the current scene collection
    bpy.context.scene.collection.objects.link(empty)
    
    # Parent Children
    for child_name in child_names:
        child = bpy.data.objects.get(child_name)
        if child:
            child.parent = empty
            child.matrix_parent_inverse = empty.matrix_world.inverted()
            
    # Animate Empty
    empty.rotation_mode = 'XYZ'
    print(f"Animating {name}...")
    for f, angle in track:
        empty.rotation_euler[axis_index] = angle
        empty.keyframe_insert(data_path="rotation_euler", frame=f)

def setup_animation():
    # Clear existing
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Import GLB
    bpy.ops.import_scene.gltf(filepath=glb_path)
    
    # Set Framerate
    bpy.context.scene.render.fps = fps
    bpy.context.scene.frame_end = total_frames
    
    # Apply Animation using Parent Empties
    
    # Peg Group (Rotate around X -> axis 0)
    create_and_animate_pivot(
        "PegPivot", 
        peg_pivot, 
        worm_track, 
        0, 
        {groups['peg_group']['names']}
    )
                
    # Wheel Group (Rotate around Z -> axis 2)
    create_and_animate_pivot(
        "WheelPivot", 
        wheel_pivot, 
        wheel_track, 
        2, 
        {groups['wheel_group']['names']}
    )

    print("Animation setup complete.")

if __name__ == "__main__":
    setup_animation()
"""
        py_filename = "tuner_anim_setup.py"
        with open(py_filename, "w") as f:
            f.write(script_content)
        print(f"  Saved script: {py_filename}")
        print("\nTo use in Blender:")
        print(f"1. Open Blender")
        print(f"2. Go to Scripting tab")
        print(f"3. Open '{py_filename}'")
        print(f"4. Run script")
        return 0

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
