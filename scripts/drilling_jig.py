#!/usr/bin/env python3
"""Drilling jig for brass guitar tuner frame.

Creates a 2-part clamshell jig for drilling holes in an N-gang frame:
1. Clamshell (top + sides) - inverted U block with M14 bushing pockets and
   printed guide holes. End walls act as end stops.
2. Base plate (removable) - bolts to clamshell bottom, guide holes for
   bottom-face drilling (wheel inlet holes).

Right-hand frame only. Uses the same config loading as build.py (--gear).

Usage:
    python scripts/drilling_jig.py --gear bh11-cd
    python scripts/drilling_jig.py --gear balanced --num-housings 3
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build123d import (
    Box,
    Part,
    Axis,
    Location,
    Cylinder,
    export_step,
)

from gib_tuners.config.defaults import (
    create_default_config,
    resolve_gear_config,
    calculate_worm_z,
    list_gear_configs,
)
from gib_tuners.config.parameters import Hand

PROJECT_ROOT = Path(__file__).parent.parent

# ============================================================
# M14 threaded bushings
# ============================================================
BUSHING_OD = 14.0           # M14 external thread diameter
BUSHING_ENGAGEMENT = 10.0   # Thread engagement depth
BUSHING_RIM = 5.0           # Minimum wall around bushing pockets

# ============================================================
# Jig dimensions (not gear-dependent)
# ============================================================
JIG_WIDTH = 40.0            # Total width (X)
END_WALL = 5.0              # End wall thickness (Y direction, acts as end stop)
CHANNEL_CLEARANCE = 0.3     # Channel oversize vs frame

TOP_SLAB = 14.0             # Thickness above pocket ceiling (for M14 top bushings)

# ============================================================
# Base plate dimensions
# ============================================================
BASE_THICKNESS = 8.0

# ============================================================
# Hardware
# ============================================================
M3_CLEARANCE = 3.4          # M3 bolt clearance hole
HEAT_INSERT_OD = 5.0        # M3 heat-set insert outer diameter
HEAT_INSERT_DEPTH = 4.0     # M3 heat-set insert height
M3_HEAD_DIA = 5.5           # M3 socket head cap screw OD
M3_HEAD_DEPTH = 3.0         # M3 socket head height


def create_clamshell(
    frame_outer, frame_length, channel_width, channel_depth,
    jig_height, side_wall, bore_depth, wall_extension,
    post_bearing_positions, worm_entry_positions, peg_bearing_positions,
    mounting_hole_positions,
    post_bearing_drill, worm_entry_drill, peg_bearing_drill, mounting_drill,
    bolt_positions,
) -> Part:
    """Create the clamshell (top + sides) with bushing pockets and guide holes.

    Inverted U cross-section: solid block with rectangular pocket from below.
    End walls act as end stops for the brass frame.
    """
    jig_length = frame_length + 2 * END_WALL

    # Solid block
    block = Box(JIG_WIDTH, jig_length, jig_height)
    block = block.move(Location((
        0,
        jig_length / 2 - END_WALL,
        (TOP_SLAB - channel_depth) / 2,
    )))

    # Cut pocket from below (frame cavity)
    pocket = Box(channel_width, frame_length, channel_depth)
    pocket = pocket.move(Location((0, frame_length / 2, -channel_depth / 2)))
    clamshell = block - pocket

    # --- Top face: post bearing bushing pockets (M14, vertical) ---
    for x, y in post_bearing_positions:
        bushing = Cylinder(BUSHING_OD / 2, TOP_SLAB + 2)
        bushing = bushing.move(Location((x, y, TOP_SLAB / 2)))
        clamshell = clamshell - bushing

    # --- Top face: mounting hole guides (printed, vertical) ---
    for y in mounting_hole_positions:
        guide = Cylinder(mounting_drill / 2, TOP_SLAB + 2)
        guide = guide.move(Location((0, y, TOP_SLAB / 2)))
        clamshell = clamshell - guide

    # --- Right wall (+X): worm entry bushing pockets (stepped: blind M14 + bore) ---
    right_outer_face = JIG_WIDTH / 2
    right_inner_face = channel_width / 2
    for y, z in worm_entry_positions:
        # Blind M14 pocket from outer face
        pocket = Cylinder(BUSHING_OD / 2, BUSHING_ENGAGEMENT)
        pocket = pocket.rotate(Axis.Y, 90)
        pocket_x = right_outer_face - BUSHING_ENGAGEMENT / 2
        pocket = pocket.move(Location((pocket_x, y, z)))
        clamshell = clamshell - pocket
        # Smaller bore from pocket bottom to inner face
        bore = Cylinder(worm_entry_drill / 2, bore_depth + 1)
        bore = bore.rotate(Axis.Y, 90)
        bore_x = right_inner_face + bore_depth / 2
        bore = bore.move(Location((bore_x, y, z)))
        clamshell = clamshell - bore

    # --- Left wall (-X): peg bearing bushing pockets (stepped: blind M14 + bore) ---
    left_outer_face = -JIG_WIDTH / 2
    left_inner_face = -channel_width / 2
    for y, z in peg_bearing_positions:
        # Blind M14 pocket from outer face
        pocket = Cylinder(BUSHING_OD / 2, BUSHING_ENGAGEMENT)
        pocket = pocket.rotate(Axis.Y, 90)
        pocket_x = left_outer_face + BUSHING_ENGAGEMENT / 2
        pocket = pocket.move(Location((pocket_x, y, z)))
        clamshell = clamshell - pocket
        # Smaller bore from pocket bottom to inner face
        bore = Cylinder(peg_bearing_drill / 2, bore_depth + 1)
        bore = bore.rotate(Axis.Y, 90)
        bore_x = left_inner_face - bore_depth / 2
        bore = bore.move(Location((bore_x, y, z)))
        clamshell = clamshell - bore

    # --- Heat-set insert holes for base plate bolts (wall bottom face) ---
    for bolt_x, bolt_y in bolt_positions:
        insert = Cylinder(HEAT_INSERT_OD / 2, HEAT_INSERT_DEPTH)
        insert = insert.move(Location((
            bolt_x,
            bolt_y,
            -channel_depth + HEAT_INSERT_DEPTH / 2,
        )))
        clamshell = clamshell - insert

    return clamshell


def create_base_plate(
    frame_length, channel_width, channel_depth,
    lip_width, lip_height,
    wheel_inlet_positions, wheel_inlet_drill,
    bolt_positions,
) -> Part:
    """Create the removable base plate with raised lip and wheel inlet guide holes.

    The lip fits inside the clamshell pocket and pushes the frame flush
    against the pocket ceiling. Bolts go through the outer flanges.
    """
    jig_length = frame_length + 2 * END_WALL

    # Outer plate (full width)
    plate = Box(JIG_WIDTH, jig_length, BASE_THICKNESS)
    plate_z = -channel_depth - BASE_THICKNESS / 2
    plate = plate.move(Location((
        0,
        jig_length / 2 - END_WALL,
        plate_z,
    )))

    # Raised lip (fits inside pocket, supports frame from below)
    lip = Box(lip_width, frame_length, lip_height)
    lip_z = -channel_depth + lip_height / 2
    lip = lip.move(Location((0, frame_length / 2, lip_z)))
    base = plate + lip

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

    return base


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
        "--num-housings", type=int, default=None,
        help="Override number of housings (default: from config, typically 5)",
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

    # Derived jig dimensions
    channel_width = frame_outer + CHANNEL_CLEARANCE
    side_wall = (JIG_WIDTH - channel_width) / 2
    bore_depth = side_wall - BUSHING_ENGAGEMENT

    # Wall extension: 5mm rim below side bushing bottom edge
    bushing_bottom_z = worm_z - BUSHING_OD / 2
    wall_extension = abs(bushing_bottom_z) - frame_outer + BUSHING_RIM
    wall_extension = max(wall_extension, 0.0)  # Don't shrink if bushing fits

    channel_depth = frame_outer + wall_extension
    jig_height = TOP_SLAB + channel_depth
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
    print(f"Creating drilling jig for gear profile '{args.gear}'...")
    print(f"  Center distance: {center_distance:.2f}mm (effective: {effective_cd:.2f}mm)")
    print(f"  Worm Z position: {worm_z:.2f}mm")
    print(f"  Frame: {frame_outer}mm outer, {frame_length}mm long, {fp.num_housings} housings")
    print(f"  Wall extension: {wall_extension:.1f}mm (channel depth: {channel_depth:.1f}mm)")
    print(f"  Drill sizes: post={post_bearing_drill}mm, worm={worm_entry_drill}mm, "
          f"peg={peg_bearing_drill}mm, mount={mounting_drill}mm, inlet={wheel_inlet_drill}mm")

    # Build geometry
    clamshell = create_clamshell(
        frame_outer=frame_outer, frame_length=frame_length,
        channel_width=channel_width, channel_depth=channel_depth,
        jig_height=jig_height, side_wall=side_wall, bore_depth=bore_depth,
        wall_extension=wall_extension,
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
        frame_length=frame_length, channel_width=channel_width,
        channel_depth=channel_depth,
        lip_width=lip_width, lip_height=lip_height,
        wheel_inlet_positions=wheel_inlet_positions,
        wheel_inlet_drill=wheel_inlet_drill,
        bolt_positions=bolt_positions,
    )

    brass_ghost = create_brass_ghost(frame_outer, frame_inner, frame_length)

    # Export STEP files
    output_dir = PROJECT_ROOT / "output" / args.gear
    output_dir.mkdir(parents=True, exist_ok=True)

    clamshell_path = output_dir / "drilling_jig_clamshell.step"
    export_step(clamshell, str(clamshell_path))
    print(f"Exported: {clamshell_path}")

    base_path = output_dir / "drilling_jig_base_plate.step"
    export_step(base_plate, str(base_path))
    print(f"Exported: {base_path}")

    # Try to show in OCP viewer
    try:
        from ocp_vscode import show_object
        show_object(clamshell, name="clamshell", options={"color": "blue"})
        show_object(base_plate, name="base_plate", options={"color": "red", "alpha": 0.5})
        show_object(brass_ghost, name="brass_frame", options={"alpha": 0.3, "color": "orange"})
        print("Sent to OCP viewer")
    except (ImportError, RuntimeError) as e:
        print(f"OCP viewer not available: {e}")


if __name__ == "__main__":
    main()
