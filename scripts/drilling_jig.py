#!/usr/bin/env python3
"""Drilling jig for brass guitar tuner frame.

Creates a 2-part clamshell jig for drilling holes in an N-gang frame:
1. Clamshell (top + sides) - inverted U block with drill guide features.
   End walls act as end stops.
2. Base plate (removable) - bolts to clamshell bottom, guide holes for
   bottom-face drilling (wheel inlet holes).

Two modes:
- production: M14 stepped bushing pockets (blind M14 + smaller bore)
- prototype: Simple through-holes at drill diameter (faster to print)

Right-hand frame only. Uses the same config loading as build.py (--gear).

Usage:
    python scripts/drilling_jig.py --gear bh11-cd
    python scripts/drilling_jig.py --gear bh11-cd --mode prototype
    python scripts/drilling_jig.py --gear balanced --num-housings 3
"""

import argparse
import sys
import warnings
from dataclasses import dataclass, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
warnings.filterwarnings("ignore", category=DeprecationWarning)

from build123d import (
    Box,
    Part,
    Axis,
    Location,
    Cylinder,
    Text,
    extrude,
    export_step,
)
import math

from gib_tuners.config.defaults import (
    create_default_config,
    resolve_gear_config,
    calculate_worm_z,
    list_gear_configs,
)
from gib_tuners.config.parameters import Hand

PROJECT_ROOT = Path(__file__).parent.parent

# ============================================================
# Jig mode configuration
# ============================================================
@dataclass(frozen=True)
class JigModeConfig:
    """Mode-dependent jig parameters."""
    name: str
    top_slab: float           # Thickness above pocket ceiling
    jig_width: float          # Total jig width (X)
    use_bushings: bool        # Whether to create M14 bushing pockets
    bushing_od: float         # M14 bushing diameter (only used if use_bushings)
    bushing_engagement: float # Thread engagement depth
    bushing_rim: float        # Min wall below bushing pockets

MODE_PRODUCTION = JigModeConfig(
    name="production",
    top_slab=14.0,
    jig_width=40.0,
    use_bushings=True,
    bushing_od=14.0,
    bushing_engagement=10.0,
    bushing_rim=5.0,
)

MODE_PROTOTYPE = JigModeConfig(
    name="prototype",
    top_slab=8.0,
    jig_width=30.0,
    use_bushings=False,
    bushing_od=0.0,
    bushing_engagement=0.0,
    bushing_rim=0.0,
)

JIG_MODES = {
    "production": MODE_PRODUCTION,
    "prototype": MODE_PROTOTYPE,
}

# ============================================================
# Jig dimensions (not gear-dependent)
# ============================================================
END_WALL = 5.0              # End wall thickness (Y direction, acts as end stop)
CHANNEL_CLEARANCE = 0.3     # Channel oversize vs frame
FRAME_LENGTH_TOLERANCE = 4.0  # Extra cavity length for plug to seat square and accommodate variation

# ============================================================
# Base plate dimensions
# ============================================================
BASE_THICKNESS = 8.0

# ============================================================
# Hardware
# ============================================================
M3_CLEARANCE = 3.4          # M3 bolt clearance hole
HEAT_INSERT_OD = 4.7        # M3 heat-set insert pocket (undersized for melt-in grip)
HEAT_INSERT_POCKET = 9.0    # Pocket depth (4mm insert + 5mm for push-in and bolt clearance)
M3_HEAD_DIA = 5.5           # M3 socket head cap screw OD
M3_HEAD_DEPTH = 3.0         # M3 socket head height

# ============================================================
# Text engraving
# ============================================================
ENGRAVE_DEPTH = 0.6         # Engraving depth into surface
FONT_SIZE = 5.3             # Text height in mm


def drill_label(diameter_mm: float) -> str:
    """Convert drill diameter to practical label (e.g. 7.05 -> 'Ø7')."""
    rounded = math.floor(diameter_mm)
    return f"Ø{rounded}"


def engrave_on_face(solid, text_str, font_size, x, y, z, rotation=0):
    """Engrave text into a horizontal face (top, facing +Z).

    Text is created in XY plane, extruded downward into the surface.
    rotation: degrees around Z axis before positioning.
    """
    txt = Text(text_str, font_size=font_size)
    txt_solid = extrude(txt, amount=ENGRAVE_DEPTH)
    if rotation != 0:
        txt_solid = txt_solid.rotate(Axis.Z, rotation)
    txt_solid = txt_solid.move(Location((x, y, z - ENGRAVE_DEPTH)))
    return solid - txt_solid


def engrave_on_bottom(solid, text_str, font_size, x, y, z):
    """Engrave text into a bottom face (facing -Z), readable from below.

    Text is mirrored so it reads correctly when viewed from underneath.
    """
    txt = Text(text_str, font_size=font_size)
    txt_solid = extrude(txt, amount=ENGRAVE_DEPTH)
    # Rotate 180° around Y to mirror for bottom-face readability
    # and flip extrusion direction into the solid
    txt_solid = txt_solid.rotate(Axis.Y, 180)
    txt_solid = txt_solid.move(Location((x, y, z + ENGRAVE_DEPTH)))
    return solid - txt_solid


def engrave_on_side(solid, text_str, font_size, x, y, z, face_dir="+X"):
    """Engrave text on a side wall face.

    face_dir: '+X' for right wall, '-X' for left wall.
    Text reads correctly when viewed from that side.
    """
    txt = Text(text_str, font_size=font_size)
    txt_solid = extrude(txt, amount=ENGRAVE_DEPTH)
    if face_dir == "+X":
        # Rotate so text faces +X, then shift inward so it cuts into wall
        txt_solid = txt_solid.rotate(Axis.Y, 90)
        txt_solid = txt_solid.move(Location((x - ENGRAVE_DEPTH, y, z)))
    elif face_dir == "-X":
        # Rotate so text faces -X (readable from left), shift inward
        txt_solid = txt_solid.rotate(Axis.Z, 180)
        txt_solid = txt_solid.rotate(Axis.Y, -90)
        txt_solid = txt_solid.move(Location((x + ENGRAVE_DEPTH, y, z)))
    return solid - txt_solid


def create_clamshell(
    mode, gear_name, frame_outer, frame_length, channel_width, channel_depth,
    jig_height, side_wall,
    post_bearing_positions, worm_entry_positions, peg_bearing_positions,
    mounting_hole_positions,
    post_bearing_drill, worm_entry_drill, peg_bearing_drill, mounting_drill,
    bolt_positions,
) -> Part:
    """Create the clamshell (top + sides) with drill guide features.

    Inverted U cross-section: solid block with rectangular pocket from below.
    End walls act as end stops for the brass frame.

    In production mode, side/top holes are M14 stepped bushing pockets.
    In prototype mode, all holes are simple through-holes at drill diameter.

    Rear end is open for removable end stop (frame slides out the back).
    """
    # Block spans from Y=-END_WALL to Y=frame_length+tolerance (no rear wall)
    # Extra cavity length lets end stop plug clamp shorter frames against front wall
    cavity_length = frame_length + FRAME_LENGTH_TOLERANCE
    jig_length = cavity_length + END_WALL

    # Solid block
    block = Box(mode.jig_width, jig_length, jig_height)
    block = block.move(Location((
        0,
        jig_length / 2 - END_WALL,
        (mode.top_slab - channel_depth) / 2,
    )))

    # Cut pocket from below (frame cavity, open at rear)
    pocket_length = cavity_length + 1  # Extend past rear face
    pocket = Box(channel_width, pocket_length, channel_depth)
    pocket = pocket.move(Location((0, pocket_length / 2, -channel_depth / 2)))
    clamshell = block - pocket

    # --- Top face: post bearing holes (vertical) ---
    if mode.use_bushings:
        # M14 through-hole for bushing
        for x, y in post_bearing_positions:
            bushing = Cylinder(mode.bushing_od / 2, mode.top_slab + 2)
            bushing = bushing.move(Location((x, y, mode.top_slab / 2)))
            clamshell = clamshell - bushing
    else:
        # Simple guide hole at drill diameter
        for x, y in post_bearing_positions:
            hole = Cylinder(post_bearing_drill / 2, mode.top_slab + 2)
            hole = hole.move(Location((x, y, mode.top_slab / 2)))
            clamshell = clamshell - hole

    # --- Top face: mounting hole guides (printed, vertical) ---
    for y in mounting_hole_positions:
        guide = Cylinder(mounting_drill / 2, mode.top_slab + 2)
        guide = guide.move(Location((0, y, mode.top_slab / 2)))
        clamshell = clamshell - guide

    # --- Right wall (+X): worm entry holes ---
    right_outer_face = mode.jig_width / 2
    right_inner_face = channel_width / 2
    if mode.use_bushings:
        # Stepped: blind M14 pocket + smaller bore
        bore_depth = side_wall - mode.bushing_engagement
        for y, z in worm_entry_positions:
            pocket = Cylinder(mode.bushing_od / 2, mode.bushing_engagement)
            pocket = pocket.rotate(Axis.Y, 90)
            pocket_x = right_outer_face - mode.bushing_engagement / 2
            pocket = pocket.move(Location((pocket_x, y, z)))
            clamshell = clamshell - pocket
            bore = Cylinder(worm_entry_drill / 2, bore_depth + 1)
            bore = bore.rotate(Axis.Y, 90)
            bore_x = right_inner_face + bore_depth / 2
            bore = bore.move(Location((bore_x, y, z)))
            clamshell = clamshell - bore
    else:
        # Simple through-hole at drill diameter
        for y, z in worm_entry_positions:
            hole = Cylinder(worm_entry_drill / 2, side_wall + 2)
            hole = hole.rotate(Axis.Y, 90)
            hole_x = right_inner_face + side_wall / 2
            hole = hole.move(Location((hole_x, y, z)))
            clamshell = clamshell - hole

    # --- Left wall (-X): peg bearing holes ---
    left_outer_face = -mode.jig_width / 2
    left_inner_face = -channel_width / 2
    if mode.use_bushings:
        # Stepped: blind M14 pocket + smaller bore
        bore_depth = side_wall - mode.bushing_engagement
        for y, z in peg_bearing_positions:
            pocket = Cylinder(mode.bushing_od / 2, mode.bushing_engagement)
            pocket = pocket.rotate(Axis.Y, 90)
            pocket_x = left_outer_face + mode.bushing_engagement / 2
            pocket = pocket.move(Location((pocket_x, y, z)))
            clamshell = clamshell - pocket
            bore = Cylinder(peg_bearing_drill / 2, bore_depth + 1)
            bore = bore.rotate(Axis.Y, 90)
            bore_x = left_inner_face - bore_depth / 2
            bore = bore.move(Location((bore_x, y, z)))
            clamshell = clamshell - bore
    else:
        # Simple through-hole at drill diameter
        for y, z in peg_bearing_positions:
            hole = Cylinder(peg_bearing_drill / 2, side_wall + 2)
            hole = hole.rotate(Axis.Y, 90)
            hole_x = left_inner_face - side_wall / 2
            hole = hole.move(Location((hole_x, y, z)))
            clamshell = clamshell - hole

    # --- Heat-set insert holes for base plate bolts (wall bottom face) ---
    for bolt_x, bolt_y in bolt_positions:
        insert = Cylinder(HEAT_INSERT_OD / 2, HEAT_INSERT_POCKET)
        insert = insert.move(Location((
            bolt_x,
            bolt_y,
            -channel_depth + HEAT_INSERT_POCKET / 2,
        )))
        clamshell = clamshell - insert

    # --- Heat-set insert holes for removable end stop (rear face of side walls) ---
    # Two bolts: one in each side wall, centered in wall thickness, mid-height
    end_stop_bolt_z = (mode.top_slab - channel_depth) / 2  # Middle of jig height
    for sign in [+1, -1]:
        bolt_x = sign * (channel_width / 2 + side_wall / 2)
        insert = Cylinder(HEAT_INSERT_OD / 2, HEAT_INSERT_POCKET)
        insert = insert.rotate(Axis.X, 90)  # Horizontal, pointing in -Y
        insert = insert.move(Location((
            bolt_x,
            cavity_length - HEAT_INSERT_POCKET / 2,
            end_stop_bolt_z,
        )))
        clamshell = clamshell - insert

    # --- Engrave labels on clamshell ---
    # "R" near rear of clamshell (where end stop attaches)
    clamshell = engrave_on_face(
        clamshell, "R", FONT_SIZE,
        x=mode.jig_width / 2 - FONT_SIZE,  # Right side, away from holes
        y=frame_length - FONT_SIZE,
        z=mode.top_slab,
    )

    # Gear name rotated along length, 3mm in from front end and left side
    gear_txt = Text(gear_name, font_size=FONT_SIZE * 0.7)
    gear_bb = gear_txt.bounding_box()
    gear_len = gear_bb.max.X - gear_bb.min.X
    gear_solid = extrude(gear_txt, amount=ENGRAVE_DEPTH)
    gear_solid = gear_solid.rotate(Axis.Z, -90)
    # Position so text starts 3mm from front face, 3mm from left side
    gear_solid = gear_solid.move(Location((
        -mode.jig_width / 2 + 3,
        -END_WALL + 3 + gear_len / 2,
        mode.top_slab - ENGRAVE_DEPTH,
    )))
    clamshell = clamshell - gear_solid

    # Label each hole type at the first housing only
    first_worm_y, first_worm_z = worm_entry_positions[0]
    first_peg_y, first_peg_z = peg_bearing_positions[0]
    first_post_x, first_post_y = post_bearing_positions[0]
    first_mount_y = mounting_hole_positions[0]

    # Right wall: worm entry drill size above first hole
    clamshell = engrave_on_side(
        clamshell, drill_label(worm_entry_drill), FONT_SIZE * 0.8,
        x=mode.jig_width / 2, y=first_worm_y,
        z=first_worm_z + FONT_SIZE * 1.5, face_dir="+X",
    )

    # Left wall: peg bearing drill size above first hole
    clamshell = engrave_on_side(
        clamshell, drill_label(peg_bearing_drill), FONT_SIZE * 0.8,
        x=-mode.jig_width / 2, y=first_peg_y,
        z=first_peg_z + FONT_SIZE * 1.5, face_dir="-X",
    )

    # Top face: post bearing drill size next to first hole
    clamshell = engrave_on_face(
        clamshell, drill_label(post_bearing_drill), FONT_SIZE * 0.8,
        x=FONT_SIZE, y=first_post_y,
        z=mode.top_slab,
    )

    # Top face: mounting hole drill size next to first mounting hole
    clamshell = engrave_on_face(
        clamshell, drill_label(mounting_drill), FONT_SIZE * 0.8,
        x=FONT_SIZE, y=first_mount_y,
        z=mode.top_slab,
    )

    return clamshell


def create_base_plate(
    mode, frame_length, channel_width, channel_depth,
    lip_width, lip_height,
    wheel_inlet_positions, wheel_inlet_drill,
    bolt_positions,
) -> Part:
    """Create the removable base plate with raised lip and wheel inlet guide holes.

    The lip fits inside the clamshell pocket and pushes the frame flush
    against the pocket ceiling. Bolts go through the outer flanges.
    In prototype mode (lip_height=0), the plate is flat with no lip.

    Matches clamshell length (front end wall only, rear is open for end stop).
    """
    jig_length = frame_length + FRAME_LENGTH_TOLERANCE + END_WALL

    # Outer plate (full width)
    plate = Box(mode.jig_width, jig_length, BASE_THICKNESS)
    plate_z = -channel_depth - BASE_THICKNESS / 2
    plate = plate.move(Location((
        0,
        jig_length / 2 - END_WALL,
        plate_z,
    )))

    # Raised lip (fits inside pocket, supports frame from below)
    if lip_height > 0:
        lip = Box(lip_width, frame_length, lip_height)
        lip_z = -channel_depth + lip_height / 2
        lip = lip.move(Location((0, frame_length / 2, lip_z)))
        base = plate + lip
    else:
        base = plate

    # Wheel inlet guide holes through lip + plate
    guide_depth = lip_height + BASE_THICKNESS + 2
    for y in wheel_inlet_positions:
        guide = Cylinder(wheel_inlet_drill / 2, guide_depth)
        guide = guide.move(Location((0, y, plate_z + (lip_height / 2))))
        base = base - guide

    # M3 bolt clearance holes + counterbores (in outer flanges)
    for bolt_x, bolt_y in bolt_positions:
        clearance = Cylinder(M3_CLEARANCE / 2, BASE_THICKNESS + 2)
        clearance = clearance.move(Location((bolt_x, bolt_y, plate_z)))
        base = base - clearance

        cb_z = -channel_depth - BASE_THICKNESS + (M3_HEAD_DEPTH + 0.5) / 2
        counterbore = Cylinder(M3_HEAD_DIA / 2, M3_HEAD_DEPTH + 0.5)
        counterbore = counterbore.move(Location((bolt_x, bolt_y, cb_z)))
        base = base - counterbore

    # Engrave wheel inlet drill size on bottom face (visible when assembled)
    if wheel_inlet_positions:
        base_bottom_z = -channel_depth - BASE_THICKNESS
        base = engrave_on_bottom(
            base, drill_label(wheel_inlet_drill), FONT_SIZE * 0.8,
            x=mode.jig_width / 4,
            y=wheel_inlet_positions[0] + FONT_SIZE * 1.5,
            z=base_bottom_z,
        )

    return base


def create_end_stop(
    mode, frame_outer, channel_width, channel_depth, side_wall, jig_height,
) -> Part:
    """Create the removable rear end stop with clamping plug.

    Bolts to rear of clamshell side walls. A 10x10mm plug protrudes into
    the cavity to push the frame against the front wall, accommodating
    up to FRAME_LENGTH_TOLERANCE variation in frame length.
    """
    # Outer dimensions match clamshell cross-section
    stop_width = mode.jig_width
    stop_height = jig_height
    stop_depth = 10.0  # Deeper than END_WALL for rigidity

    # Start with solid block
    stop = Box(stop_width, stop_depth, stop_height)
    stop = stop.move(Location((0, stop_depth / 2, (mode.top_slab - channel_depth) / 2)))

    # Plug that protrudes into cavity (pushes frame against front wall)
    plug_size = frame_outer  # 10x10mm matches frame outer
    plug_length = FRAME_LENGTH_TOLERANCE + 1.0  # Extends past tolerance range
    plug = Box(plug_size, plug_length, plug_size)
    plug = plug.move(Location((0, -plug_length / 2, -channel_depth / 2)))
    stop = stop + plug

    # M3 bolt clearance holes with counterbores (through the side wings)
    end_stop_bolt_z = (mode.top_slab - channel_depth) / 2  # Match clamshell inserts
    for sign in [+1, -1]:
        bolt_x = sign * (channel_width / 2 + side_wall / 2)
        # Clearance hole through full depth
        clearance = Cylinder(M3_CLEARANCE / 2, stop_depth + 2)
        clearance = clearance.rotate(Axis.X, 90)
        clearance = clearance.move(Location((bolt_x, stop_depth / 2, end_stop_bolt_z)))
        stop = stop - clearance
        # Counterbore on rear face
        counterbore = Cylinder(M3_HEAD_DIA / 2, M3_HEAD_DEPTH + 0.5)
        counterbore = counterbore.rotate(Axis.X, 90)
        counterbore = counterbore.move(Location((
            bolt_x,
            stop_depth - (M3_HEAD_DEPTH + 0.5) / 2,
            end_stop_bolt_z,
        )))
        stop = stop - counterbore

    return stop


def create_brass_ghost(frame_outer, frame_inner, frame_length) -> Part:
    """Create transparent brass frame for visualization."""
    outer = Box(frame_outer, frame_length, frame_outer)
    inner = Box(frame_inner, frame_length + 2, frame_inner)
    ghost = outer - inner
    ghost = ghost.move(Location((0, frame_length / 2, -frame_outer / 2)))
    return ghost


def main():
    parser = argparse.ArgumentParser(
        description="Drilling jig for brass tuner frame",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--gear", type=str, required=True,
        help="Gear config name (e.g., 'bh11-cd'). Use --list-gears to see options.",
    )
    parser.add_argument(
        "-n", "--num-housings", type=int, default=None,
        help="Override number of housings (default: from config, typically 5)",
    )
    parser.add_argument(
        "--mode", choices=list(JIG_MODES.keys()), default="production",
        help="Jig mode: 'production' (M14 bushing pockets) or 'prototype' (simple guide holes)",
    )
    parser.add_argument(
        "--list-gears", action="store_true",
        help="List available gear configurations and exit",
    )

    # Handle --list-gears before requiring --gear
    if "--list-gears" in sys.argv:
        configs = list_gear_configs()
        print("Available gear configs:", ", ".join(configs) if configs else "(none)")
        return

    args = parser.parse_args()

    # Load config using same path as build.py
    gear_paths = resolve_gear_config(args.gear)
    config = create_default_config(
        scale=1.0,
        tolerance="production",
        hand=Hand.RIGHT,
        gear_json_path=gear_paths.json_path,
        config_dir=gear_paths.config_dir,
    )

    # Override num_housings if specified
    if args.num_housings is not None:
        config = replace(config, frame=replace(config.frame, num_housings=args.num_housings))

    # Extract frame parameters
    fp = config.frame
    frame_outer = fp.box_outer
    frame_inner = fp.box_inner
    frame_length = fp.total_length
    frame_wall = fp.wall_thickness

    # Extract gear-dependent values
    center_distance = config.gear.center_distance
    extra_backlash = config.gear.extra_backlash
    effective_cd = center_distance - extra_backlash
    cd_half = effective_cd / 2
    worm_z = calculate_worm_z(config)

    # Extract hole diameters (nominal, no tolerance applied — jig guides the drill)
    post_bearing_drill = fp.post_bearing_hole
    worm_entry_drill = fp.worm_entry_hole
    peg_bearing_drill = fp.peg_bearing_hole
    mounting_drill = fp.mounting_hole
    wheel_inlet_drill = fp.wheel_inlet_hole

    # Resolve jig mode
    mode = JIG_MODES[args.mode]

    # Derived jig dimensions
    channel_width = frame_outer + CHANNEL_CLEARANCE
    side_wall = (mode.jig_width - channel_width) / 2

    # Wall extension below frame bottom
    if mode.use_bushings:
        # Production: ensure bushing_rim below side bushing bottom edge
        bushing_bottom_z = worm_z - mode.bushing_od / 2
        wall_extension = abs(bushing_bottom_z) - frame_outer + mode.bushing_rim
        wall_extension = max(wall_extension, 0.0)
    else:
        # Prototype: 3mm below frame for structural support around side holes
        wall_extension = 3.0

    channel_depth = frame_outer + wall_extension
    jig_height = mode.top_slab + channel_depth
    lip_width = frame_outer  # Fits snugly inside channel
    lip_height = wall_extension

    # Compute positions
    housing_centers = list(fp.housing_centers)
    mounting_hole_positions = list(fp.mounting_hole_positions)

    post_bearing_positions = [(0, hc - cd_half) for hc in housing_centers]
    worm_entry_positions = [(hc + cd_half, worm_z) for hc in housing_centers]
    peg_bearing_positions = list(worm_entry_positions)
    wheel_inlet_positions = [hc - cd_half for hc in housing_centers]

    bolt_x_offset = channel_width / 2 + side_wall / 2
    bolt_positions = [
        (+bolt_x_offset, 5.0),
        (+bolt_x_offset, frame_length - 5.0),
        (-bolt_x_offset, 5.0),
        (-bolt_x_offset, frame_length - 5.0),
    ]

    # Print summary
    print(f"Creating drilling jig ({mode.name}) for gear profile '{args.gear}'...")
    print(f"  Center distance: {center_distance:.2f}mm (effective: {effective_cd:.2f}mm)")
    print(f"  Worm Z position: {worm_z:.2f}mm")
    print(f"  Frame: {frame_outer}mm outer, {frame_length}mm long, {fp.num_housings} housings")
    print(f"  Jig: {mode.jig_width}mm wide, {jig_height:.1f}mm tall, "
          f"wall extension: {wall_extension:.1f}mm")
    if mode.use_bushings:
        print(f"  Bushings: M14 stepped pockets, {side_wall:.1f}mm side wall")
    else:
        print(f"  Guide holes: simple through-holes, {side_wall:.1f}mm side wall")
    print(f"  Drill sizes: post={post_bearing_drill}mm, worm={worm_entry_drill}mm, "
          f"peg={peg_bearing_drill}mm, mount={mounting_drill}mm, inlet={wheel_inlet_drill}mm")

    # Build geometry
    clamshell = create_clamshell(
        mode=mode, gear_name=args.gear,
        frame_outer=frame_outer, frame_length=frame_length,
        channel_width=channel_width, channel_depth=channel_depth,
        jig_height=jig_height, side_wall=side_wall,
        post_bearing_positions=post_bearing_positions,
        worm_entry_positions=worm_entry_positions,
        peg_bearing_positions=peg_bearing_positions,
        mounting_hole_positions=mounting_hole_positions,
        post_bearing_drill=post_bearing_drill,
        worm_entry_drill=worm_entry_drill,
        peg_bearing_drill=peg_bearing_drill,
        mounting_drill=mounting_drill,
        bolt_positions=bolt_positions,
    )

    base_plate = create_base_plate(
        mode=mode,
        frame_length=frame_length, channel_width=channel_width,
        channel_depth=channel_depth,
        lip_width=lip_width, lip_height=lip_height,
        wheel_inlet_positions=wheel_inlet_positions,
        wheel_inlet_drill=wheel_inlet_drill,
        bolt_positions=bolt_positions,
    )

    end_stop = create_end_stop(
        mode=mode, frame_outer=frame_outer,
        channel_width=channel_width, channel_depth=channel_depth,
        side_wall=side_wall, jig_height=jig_height,
    )

    brass_ghost = create_brass_ghost(frame_outer, frame_inner, frame_length)

    # Export STEP files
    output_dir = PROJECT_ROOT / "output" / args.gear
    output_dir.mkdir(parents=True, exist_ok=True)

    clamshell_path = output_dir / f"drilling_jig_clamshell_{mode.name}.step"
    export_step(clamshell, str(clamshell_path))
    print(f"Exported: {clamshell_path}")

    base_path = output_dir / f"drilling_jig_base_plate_{mode.name}.step"
    export_step(base_plate, str(base_path))
    print(f"Exported: {base_path}")

    end_stop_path = output_dir / f"drilling_jig_end_stop_{mode.name}.step"
    export_step(end_stop, str(end_stop_path))
    print(f"Exported: {end_stop_path}")

    # Try to show in OCP viewer
    try:
        from ocp_vscode import show_object
        show_object(clamshell, name="clamshell", options={"color": "blue"})
        show_object(base_plate, name="base_plate", options={"color": "red", "alpha": 0.5})
        # Position end stop at rear of clamshell
        cavity_length = frame_length + FRAME_LENGTH_TOLERANCE
        end_stop_positioned = end_stop.move(Location((0, cavity_length, 0)))
        show_object(end_stop_positioned, name="end_stop", options={"color": "green", "alpha": 0.7})
        show_object(brass_ghost, name="brass_frame", options={"alpha": 0.3, "color": "orange"})
        print("Sent to OCP viewer")
    except (ImportError, RuntimeError) as e:
        print(f"OCP viewer not available: {e}")


if __name__ == "__main__":
    main()
