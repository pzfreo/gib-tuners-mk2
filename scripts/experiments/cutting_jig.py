#!/usr/bin/env python3
"""Prototype cutting jig for brass frame manufacturing.

Creates a jig to:
1. Cut brass stock to 145mm length
2. Guide vertical saw cuts for gaps between housings

Usage:
    python scripts/experiments/cutting_jig.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from build123d import (
    Box,
    Part,
    Axis,
    Location,
    Cylinder,
    export_step,
)

# Jig parameters
JIG_LENGTH = 185.0  # 145mm frame + 10mm end stop + 30mm extra for end stop travel
JIG_WIDTH = 30.0    # Wide enough for stability, thick side walls
FLOOR_THICKNESS = 8.0   # Thick floor for robustness

CHANNEL_WIDTH = 10.3   # 10mm brass + 0.3mm clearance
CHANNEL_DEPTH = 10.0   # Matches brass box height - sits flush with jig top
WALL_THICKNESS = (JIG_WIDTH - CHANNEL_WIDTH) / 2  # Side walls

JIG_HEIGHT = CHANNEL_DEPTH + FLOOR_THICKNESS  # Derived from floor + channel

END_STOP_LENGTH = 10.0  # Solid end stop at Y=0

SAW_SLOT_WIDTH = 1.0   # Slot for slitting saw
SAW_KERF = 1.0         # Saw blade kerf (material removed)

# Cut depths
PARTIAL_CUT_DEPTH = 8.9   # Cuts through top wall + void, leaves bottom wall (10 - 1.1)
FULL_CUT_DEPTH = 10.0     # Cuts all the way through brass (matches brass height)

# Moveable end stop parameters
INNER_PLUG_SIZE = 7.7     # Fits inside brass tube (7.8mm inner)
BRASS_WALL = 1.1          # Brass tube wall thickness
BRASS_OUTER = 10.0        # Brass tube outer dimension
INNER_PLUG_LENGTH = 5.0   # How far plug extends into brass
OUTER_BODY_SIZE = 9.9     # Sits against brass end (just under 10mm)
OUTER_BODY_Y_LENGTH = 25.0  # Length of body in Y direction (for sturdiness)
M5_CLEARANCE = 5.5        # M5 bolt clearance hole
M5_SLOT_WIDTH = 5.5       # Slot width in jig base for adjustment
HEAT_INSERT_OD = 6.4      # M5 heat-set insert outer diameter (typical)

# Frame dimensions (from spec)
FRAME_LENGTH = 145.0
HOUSING_LENGTH = 16.2
TUNER_PITCH = 27.2
END_LENGTH = 10.0

# Gap locations (Y start, Y end) - where vertical cuts are needed
GAPS = [
    (0.0, 10.0),       # End 1
    (26.2, 37.2),      # Gap 1-2
    (53.4, 64.4),      # Gap 2-3
    (80.6, 91.6),      # Gap 3-4
    (107.8, 118.8),    # Gap 4-5
    (135.0, 145.0),    # End 2
]


def create_end_stop():
    """Create the moveable end stop.

    Sits inside the jig channel on the channel floor:
    - Inner plug: 7.7mm square x 5mm - extends in -Y direction into brass tube
    - Outer body: 9.9mm x 25mm (Y) - sits on channel floor, flush with jig top
    - M5 clearance hole through body for bolt into heat-set insert in jig floor
    """
    # Body height: sits on channel floor (Z=-CHANNEL_DEPTH) up to jig top (Z=0)
    body_height = CHANNEL_DEPTH  # 10mm

    # Outer body (sits on channel floor)
    # Extended in Y direction for sturdiness
    body = Box(OUTER_BODY_SIZE, OUTER_BODY_Y_LENGTH, body_height)
    # Position so bottom is on channel floor (Z=-CHANNEL_DEPTH), top at Z=0
    # Front face (toward brass) at Y=0
    body = body.move(Location((0, OUTER_BODY_Y_LENGTH/2, -body_height/2)))

    # Plug (extends into brass tube in -Y direction)
    # Plug must be CENTERED in the inner cavity of the brass tube
    inner_bottom_z = -CHANNEL_DEPTH + BRASS_WALL  # -9.9
    inner_top_z = -CHANNEL_DEPTH + BRASS_OUTER - BRASS_WALL  # -2.1
    plug_center_z = (inner_bottom_z + inner_top_z) / 2  # Center of inner cavity
    plug = Box(INNER_PLUG_SIZE, INNER_PLUG_LENGTH, INNER_PLUG_SIZE)
    plug = plug.move(Location((0, -INNER_PLUG_LENGTH/2, plug_center_z)))

    end_stop = body + plug

    # M5 clearance hole through the body (vertical, for bolt into heat-set insert below)
    # Position hole in center of body
    bolt_hole = Cylinder(M5_CLEARANCE/2, body_height + 2)
    bolt_hole = bolt_hole.move(Location((0, OUTER_BODY_Y_LENGTH/2, -body_height/2)))
    end_stop = end_stop - bolt_hole

    return end_stop


def create_cutting_jig() -> Part:
    """Create the cutting jig geometry."""

    # Start with solid block
    jig = Box(JIG_WIDTH, JIG_LENGTH, JIG_HEIGHT)

    # Move so Y=0 is at end stop, X centered, Z=0 at top
    jig = jig.move(Location((0, JIG_LENGTH/2 - END_STOP_LENGTH, -JIG_HEIGHT/2)))

    # Cut the channel (U-shape for brass to sit in)
    # Channel opens at TOP (Z=0) for saw access, floor at bottom
    # Channel runs from Y=0 (after end stop) to Y=155 (end of jig)
    channel_length = JIG_LENGTH - END_STOP_LENGTH
    channel = Box(CHANNEL_WIDTH, channel_length, CHANNEL_DEPTH)
    channel = channel.move(Location((0, channel_length/2, -CHANNEL_DEPTH/2)))
    jig = jig - channel

    # Cut 1mm saw guide slots at each gap boundary
    # Offset slots so kerf falls OUTSIDE the housing sections (into the gaps)
    # gap_start = housing ends, gap begins -> offset slot INTO gap (+kerf/2)
    # gap_end = gap ends, housing begins -> offset slot INTO gap (-kerf/2)

    saw_cuts = []  # (y_position, is_full_depth)

    for gap_start, gap_end in GAPS:
        if gap_start > 0:  # Skip Y=0 at end stop
            # Housing ends here, gap begins - offset into gap
            saw_cuts.append((gap_start + SAW_KERF/2, False))
        if gap_end < FRAME_LENGTH:
            # Gap ends here, housing begins - offset into gap
            saw_cuts.append((gap_end - SAW_KERF/2, False))

    # Add full-depth end cut at 145mm (kerf falls outside, into waste)
    saw_cuts.append((FRAME_LENGTH + SAW_KERF/2, True))

    for y_pos, is_full_depth in saw_cuts:
        cut_depth = FULL_CUT_DEPTH if is_full_depth else PARTIAL_CUT_DEPTH
        # Channel opens at top (Z=0), brass sits flush with top (Z=0 to Z=-10)
        # Slots cut through side walls from top, allowing saw to reach brass
        slot_depth = cut_depth
        saw_slot = Box(JIG_WIDTH + 2, SAW_SLOT_WIDTH, slot_depth + 1)
        saw_slot = saw_slot.move(Location((
            0,
            y_pos,
            -slot_depth / 2 + 0.5  # Start slightly above Z=0
        )))
        jig = jig - saw_slot

    # Fixed end plug - extends from end stop into brass tube to hold it down
    # Plug at Y=0 (end stop face) extending in +Y direction into brass
    # Plug must be CENTERED in the inner cavity of the brass tube
    # Brass sits on channel floor at Z = -CHANNEL_DEPTH
    fixed_plug_length = 3.0
    inner_bottom_z = -CHANNEL_DEPTH + BRASS_WALL  # -9.9
    inner_top_z = -CHANNEL_DEPTH + BRASS_OUTER - BRASS_WALL  # -2.1
    plug_center_z = (inner_bottom_z + inner_top_z) / 2  # Center of inner cavity
    fixed_plug = Box(INNER_PLUG_SIZE, fixed_plug_length, INNER_PLUG_SIZE)
    fixed_plug = fixed_plug.move(Location((
        0,
        fixed_plug_length/2,  # Starts at Y=0, extends to Y=3
        plug_center_z
    )))
    jig = jig + fixed_plug

    # Bolt clearance hole through channel floor + heat-set insert hole in jig floor
    # End stop body is 25mm in Y, bolt hole is in center, so 12.5mm from front face
    # With end stop front face at Y=145 (frame end), bolt at Y=145+12.5=157.5
    insert_y = FRAME_LENGTH + OUTER_BODY_Y_LENGTH/2

    # M5 clearance hole through channel floor (for bolt to pass through)
    bolt_clearance = Cylinder(M5_CLEARANCE/2, CHANNEL_DEPTH + 1)
    bolt_clearance = bolt_clearance.move(Location((
        0,
        insert_y,
        -CHANNEL_DEPTH/2
    )))
    jig = jig - bolt_clearance

    # Heat-set insert hole in solid floor below
    insert_hole = Cylinder(HEAT_INSERT_OD/2, FLOOR_THICKNESS + 1)
    insert_hole = insert_hole.move(Location((
        0,
        insert_y,
        -CHANNEL_DEPTH - FLOOR_THICKNESS/2
    )))
    jig = jig - insert_hole

    return jig


def main():
    print("Creating cutting jig prototype...")

    jig = create_cutting_jig()
    end_stop = create_end_stop()

    # Position end stop in the channel for visualization
    # End stop front face at Y=FRAME_LENGTH (145mm), body extends in +Y
    end_stop_positioned = end_stop.move(Location((0, FRAME_LENGTH, 0)))

    # Export STEP
    output_dir = Path(__file__).parent.parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    step_path = output_dir / "cutting_jig_prototype.step"
    export_step(jig, str(step_path))
    print(f"Exported: {step_path}")

    end_stop_path = output_dir / "cutting_jig_end_stop.step"
    export_step(end_stop, str(end_stop_path))
    print(f"Exported: {end_stop_path}")

    # Create ghost of brass frame for visualization (hollow box section)
    brass_inner = BRASS_OUTER - 2 * BRASS_WALL  # 7.8mm inner
    brass_outer_box = Box(BRASS_OUTER, FRAME_LENGTH, BRASS_OUTER)
    brass_inner_box = Box(brass_inner, FRAME_LENGTH + 2, brass_inner)
    brass_ghost = brass_outer_box - brass_inner_box
    brass_ghost = brass_ghost.move(Location((0, FRAME_LENGTH/2, -CHANNEL_DEPTH + BRASS_OUTER/2)))

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
