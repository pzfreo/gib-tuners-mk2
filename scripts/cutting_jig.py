#!/usr/bin/env python3
"""Cutting jig for brass frame manufacturing.

Creates a jig to:
1. Cut brass stock to length
2. Guide vertical saw cuts for gaps between housings

Frame dimensions are read from the JSON for the selected gear definition.
Uses the same --gear argument and config loading as build.py.

Usage:
    python scripts/cutting_jig.py --gear bh11-cd
    python scripts/cutting_jig.py --gear balanced --num-housings 3
"""

import argparse
import sys
import warnings
from dataclasses import replace
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
    chamfer,
    extrude,
    export_step,
)

from gib_tuners.config.defaults import (
    create_default_config,
    resolve_gear_config,
    list_gear_configs,
)
from gib_tuners.config.parameters import Hand

PROJECT_ROOT = Path(__file__).parent.parent

# ============================================================
# Jig dimensions (not frame-dependent)
# ============================================================
JIG_WIDTH = 30.0            # Wide enough for stability
FLOOR_THICKNESS = 8.0       # Thick floor for robustness
CHANNEL_CLEARANCE = 0.1     # Channel oversize vs frame (per axis)
END_STOP_LENGTH = 10.0      # Solid end stop at Y=0
END_STOP_TRAVEL = 30.0      # Extra length for moveable end stop

SAW_SLOT_WIDTH = 1.0        # Slot for slitting saw
SAW_KERF = 1.0              # Saw blade kerf (material removed)

# ============================================================
# Moveable end stop parameters
# ============================================================
PLUG_CLEARANCE = 0.1        # Clearance per side for inner plug
INNER_PLUG_LENGTH = 5.0     # How far plug extends into brass
OUTER_BODY_CLEARANCE = 0.1  # Body slightly under frame outer
OUTER_BODY_Y_LENGTH = 25.0  # Length of body in Y direction (for sturdiness)
FIXED_PLUG_LENGTH = 3.0     # Fixed plug extends 3mm into brass

# ============================================================
# Hardware
# ============================================================
M3_CLEARANCE = 3.4          # M3 bolt clearance hole
M3_HEAD_DIA = 5.5           # M3 socket head cap screw OD
M3_HEAD_DEPTH = 3.0         # M3 socket head height
HEAT_INSERT_OD = 4.7        # M3 heat-set insert pocket (undersized for melt-in grip)
HEAT_INSERT_POCKET = 9.0    # Pocket depth (4mm insert + 5mm for push-in and bolt clearance)


def compute_gaps(housing_centers, housing_length, frame_length):
    """Compute gap regions (Y start, Y end) from housing centers.

    Returns list of (gap_start, gap_end) tuples including end regions.
    """
    half = housing_length / 2
    gaps = []

    # Before first housing
    first_start = housing_centers[0] - half
    if first_start > 0:
        gaps.append((0.0, first_start))

    # Between housings
    for i in range(len(housing_centers) - 1):
        gap_start = housing_centers[i] + half
        gap_end = housing_centers[i + 1] - half
        gaps.append((gap_start, gap_end))

    # After last housing
    last_end = housing_centers[-1] + half
    if last_end < frame_length:
        gaps.append((last_end, frame_length))

    return gaps


def create_end_stop(frame_outer, frame_wall):
    """Create the moveable end stop.

    Sits inside the jig channel on the channel floor:
    - Inner plug extends in -Y direction into brass tube
    - Outer body sits on channel floor, flush with jig top
    - M5 clearance hole through body for bolt into heat-set insert in jig floor
    """
    channel_depth = frame_outer + CHANNEL_CLEARANCE
    frame_inner = frame_outer - 2 * frame_wall
    inner_plug_size = frame_inner - 2 * PLUG_CLEARANCE
    outer_body_size = frame_outer - OUTER_BODY_CLEARANCE

    body_height = channel_depth

    # Outer body (sits on channel floor)
    body = Box(outer_body_size, OUTER_BODY_Y_LENGTH, body_height)
    body = body.move(Location((0, OUTER_BODY_Y_LENGTH / 2, -body_height / 2)))

    # Plug (extends into brass tube in -Y direction)
    # Centered in brass inner cavity
    inner_bottom_z = -channel_depth + frame_wall
    inner_top_z = -channel_depth + frame_outer - frame_wall
    plug_center_z = (inner_bottom_z + inner_top_z) / 2
    plug = Box(inner_plug_size, INNER_PLUG_LENGTH, inner_plug_size)

    # 45° chamfer on exposed bottom edges (eliminates support material trap)
    chamfer_size = channel_depth - (frame_outer - frame_wall)
    if chamfer_size > 0.1:
        bottom_edges = plug.edges().filter_by_position(
            Axis.Z, -inner_plug_size / 2 - 0.01, -inner_plug_size / 2 + 0.01
        )
        # Exclude edge at Y=+INNER_PLUG_LENGTH/2 (joins body)
        exposed = [e for e in bottom_edges if e.bounding_box().min.Y < INNER_PLUG_LENGTH / 2 - 0.01]
        plug = chamfer(exposed, length=chamfer_size)

    plug = plug.move(Location((0, -INNER_PLUG_LENGTH / 2, plug_center_z)))

    end_stop = body + plug

    # M3 clearance hole through body with counterbore for bolt head
    bolt_y = OUTER_BODY_Y_LENGTH / 2
    bolt_hole = Cylinder(M3_CLEARANCE / 2, body_height + 2)
    bolt_hole = bolt_hole.move(Location((0, bolt_y, -body_height / 2)))
    counterbore = Cylinder(M3_HEAD_DIA / 2, M3_HEAD_DEPTH + 0.5)
    counterbore = counterbore.move(Location((0, bolt_y, -(M3_HEAD_DEPTH + 0.5) / 2)))
    end_stop = end_stop - bolt_hole - counterbore

    return end_stop


ENGRAVE_DEPTH = 0.6
FONT_SIZE = 5.3


def create_cutting_jig(frame_outer, frame_wall, frame_length, gaps, gear_name=""):
    """Create the cutting jig geometry.

    All frame dimensions derived from config.
    """
    channel_width = frame_outer + CHANNEL_CLEARANCE
    channel_depth = frame_outer + CHANNEL_CLEARANCE
    jig_height = channel_depth + FLOOR_THICKNESS
    jig_length = frame_length + END_STOP_LENGTH + END_STOP_TRAVEL

    frame_inner = frame_outer - 2 * frame_wall
    inner_plug_size = frame_inner - 2 * PLUG_CLEARANCE
    partial_cut_depth = frame_outer - frame_wall
    full_cut_depth = frame_outer

    # Start with solid block
    jig = Box(JIG_WIDTH, jig_length, jig_height)
    jig = jig.move(Location((0, jig_length / 2 - END_STOP_LENGTH, -jig_height / 2)))

    # Cut the channel (U-shape for brass to sit in)
    channel_length = jig_length - END_STOP_LENGTH
    channel = Box(channel_width, channel_length, channel_depth)
    channel = channel.move(Location((0, channel_length / 2, -channel_depth / 2)))
    jig = jig - channel

    # Cut saw guide slots at each gap boundary
    # Offset so kerf falls OUTSIDE housing sections (into gaps)
    saw_cuts = []  # (y_position, is_full_depth)

    for gap_start, gap_end in gaps:
        if gap_start > 0:  # Skip Y=0 at end stop
            saw_cuts.append((gap_start + SAW_KERF / 2, False))
        if gap_end < frame_length:
            saw_cuts.append((gap_end - SAW_KERF / 2, False))

    # Full-depth end cut (kerf falls outside, into waste)
    saw_cuts.append((frame_length + SAW_KERF / 2, True))

    for y_pos, is_full_depth in saw_cuts:
        cut_depth = full_cut_depth if is_full_depth else partial_cut_depth
        saw_slot = Box(JIG_WIDTH + 2, SAW_SLOT_WIDTH, cut_depth + 1)
        saw_slot = saw_slot.move(Location((
            0,
            y_pos,
            -cut_depth / 2 + 0.5,
        )))
        jig = jig - saw_slot

    # Fixed end plug at Y=0
    inner_bottom_z = -channel_depth + frame_wall
    inner_top_z = -channel_depth + frame_outer - frame_wall
    plug_center_z = (inner_bottom_z + inner_top_z) / 2
    fixed_plug = Box(inner_plug_size, FIXED_PLUG_LENGTH, inner_plug_size)

    # 45° chamfer on exposed bottom edges (eliminates support material trap)
    chamfer_size = channel_depth - (frame_outer - frame_wall)
    if chamfer_size > 0.1:
        bottom_edges = fixed_plug.edges().filter_by_position(
            Axis.Z, -inner_plug_size / 2 - 0.01, -inner_plug_size / 2 + 0.01
        )
        # Exclude back edge (at Y=-FIXED_PLUG_LENGTH/2, embedded in end wall)
        exposed = [e for e in bottom_edges if e.bounding_box().max.Y > -FIXED_PLUG_LENGTH / 2 + 0.01]
        fixed_plug = chamfer(exposed, length=chamfer_size)

    fixed_plug = fixed_plug.move(Location((
        0,
        FIXED_PLUG_LENGTH / 2,
        plug_center_z,
    )))
    jig = jig + fixed_plug

    # Bolt clearance hole + heat-set insert for moveable end stop
    insert_y = frame_length + OUTER_BODY_Y_LENGTH / 2

    bolt_clearance = Cylinder(M3_CLEARANCE / 2, channel_depth + 1)
    bolt_clearance = bolt_clearance.move(Location((0, insert_y, -channel_depth / 2)))
    jig = jig - bolt_clearance

    insert_hole = Cylinder(HEAT_INSERT_OD / 2, HEAT_INSERT_POCKET)
    insert_z = -channel_depth - (HEAT_INSERT_POCKET) / 2
    insert_hole = insert_hole.move(Location((0, insert_y, insert_z)))
    jig = jig - insert_hole

    # Engrave gear name on bottom face (readable when flipped over)
    if gear_name:
        jig_bottom_z = -channel_depth - FLOOR_THICKNESS
        txt = Text(gear_name, font_size=FONT_SIZE * 0.7)
        txt_solid = extrude(txt, amount=ENGRAVE_DEPTH)
        txt_solid = txt_solid.rotate(Axis.Z, 90)
        # Mirror for bottom-face readability
        txt_solid = txt_solid.rotate(Axis.Y, 180)
        txt_solid = txt_solid.move(Location((
            0,
            frame_length / 2,
            jig_bottom_z + ENGRAVE_DEPTH,
        )))
        jig = jig - txt_solid

    return jig


def main():
    parser = argparse.ArgumentParser(
        description="Cutting jig for brass tuner frame",
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
    frame_wall = fp.wall_thickness
    frame_length = fp.total_length
    housing_centers = list(fp.housing_centers)
    housing_length = fp.housing_length

    # Compute gap regions
    gaps = compute_gaps(housing_centers, housing_length, frame_length)

    # Derived dimensions for summary
    channel_width = frame_outer + CHANNEL_CLEARANCE
    partial_cut_depth = frame_outer - frame_wall
    jig_length = frame_length + END_STOP_LENGTH + END_STOP_TRAVEL

    # Print summary
    print(f"Creating cutting jig for gear profile '{args.gear}'...")
    print(f"  Frame: {frame_outer}mm outer, {frame_wall}mm wall, "
          f"{frame_length}mm long, {fp.num_housings} housings")
    channel_depth = frame_outer + CHANNEL_CLEARANCE
    print(f"  Channel: {channel_width}mm wide x {channel_depth}mm deep")
    print(f"  Jig: {JIG_WIDTH}mm x {jig_length}mm x {channel_depth + FLOOR_THICKNESS}mm")
    print(f"  Partial cut depth: {partial_cut_depth}mm (leaves {frame_wall}mm bottom wall)")
    print(f"  Gaps: {len(gaps)} regions, {len(gaps) * 2 - 1} saw slots + 1 end cut")

    # Build geometry
    jig = create_cutting_jig(frame_outer, frame_wall, frame_length, gaps, gear_name=args.gear)
    end_stop = create_end_stop(frame_outer, frame_wall)

    # Position end stop for visualization
    end_stop_positioned = end_stop.move(Location((0, frame_length, 0)))

    # Create ghost of brass frame for visualization
    brass_outer_box = Box(frame_outer, frame_length, frame_outer)
    brass_inner_box = Box(frame_inner, frame_length + 2, frame_inner)
    brass_ghost = brass_outer_box - brass_inner_box
    brass_ghost = brass_ghost.move(Location((
        0, frame_length / 2, -frame_outer + frame_outer / 2,
    )))

    # Export STEP files
    output_dir = PROJECT_ROOT / "output" / args.gear
    output_dir.mkdir(parents=True, exist_ok=True)

    step_path = output_dir / "cutting_jig_prototype.step"
    export_step(jig, str(step_path))
    print(f"Exported: {step_path}")

    end_stop_path = output_dir / "cutting_jig_end_stop.step"
    export_step(end_stop, str(end_stop_path))
    print(f"Exported: {end_stop_path}")

    # Try to show in OCP viewer
    try:
        from ocp_vscode import show_object
        show_object(jig, name="cutting_jig", options={"color": "blue"})
        show_object(end_stop_positioned, name="end_stop")
        show_object(brass_ghost, name="brass_frame", options={"alpha": 0.3, "color": "orange"})
        print("Sent to OCP viewer")
    except (ImportError, RuntimeError) as e:
        print(f"OCP viewer not available: {e}")


if __name__ == "__main__":
    main()
