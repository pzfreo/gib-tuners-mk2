#!/usr/bin/env python3
"""Debug script to visualize peg head positioning in frame."""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
warnings.filterwarnings("ignore", category=DeprecationWarning)

from build123d import Location, Axis, Box, Align

from gib_tuners.config.defaults import create_default_config
from gib_tuners.components.peg_head import create_peg_head
from gib_tuners.components.frame import create_frame


def main() -> int:
    try:
        from ocp_vscode import show_object
    except ImportError:
        print("Error: ocp-vscode not installed")
        return 1

    config = create_default_config()

    # Frame dimensions
    frame_params = config.frame
    box_outer = frame_params.box_outer
    wall = frame_params.wall_thickness
    center_distance = config.gear.center_distance

    print(f"Frame: {box_outer}mm outer, {wall}mm walls")
    print(f"Cavity: {frame_params.box_inner}mm")
    print(f"Center distance: {center_distance}mm")

    # Create single housing frame for debugging
    # Use num_housings=1 for simpler visualization
    from gib_tuners.config.parameters import FrameParams, BuildConfig
    single_frame_params = FrameParams(
        box_outer=box_outer,
        wall_thickness=wall,
        num_housings=1,
    )
    single_config = BuildConfig(frame=single_frame_params)

    # Create frame
    from gib_tuners.components.frame import create_frame
    frame = create_frame(single_config)

    # Create peg head - first without worm to see base geometry
    peg_head_no_worm = create_peg_head(config, include_worm=False)
    bb_no_worm = peg_head_no_worm.bounding_box()
    print(f"\nPeg head (no worm) bounding box:")
    print(f"  X: {bb_no_worm.min.X:.2f} to {bb_no_worm.max.X:.2f}")

    # Now with worm
    peg_head = create_peg_head(config, include_worm=True)

    # Peg head after rotation:
    # - Shaft along X (toward +X after -90° Y rotation)
    # - Pip at -X (outside)
    # - Ring approximately at X=0

    # Get peg head bounding box to understand its position
    bb = peg_head.bounding_box()
    print(f"\nPeg head bounding box:")
    print(f"  X: {bb.min.X:.2f} to {bb.max.X:.2f} (size: {bb.max.X - bb.min.X:.2f})")
    print(f"  Y: {bb.min.Y:.2f} to {bb.max.Y:.2f} (size: {bb.max.Y - bb.min.Y:.2f})")
    print(f"  Z: {bb.min.Z:.2f} to {bb.max.Z:.2f} (size: {bb.max.Z - bb.min.Z:.2f})")

    # Worm axis should be:
    # - At Z = -box_outer/2 (centered in frame cavity)
    # - At Y = +center_distance/2 from housing center (per spec)
    # - For RH: worm entry on +X side, shaft exits -X side

    worm_z = -box_outer / 2

    # Housing center for single housing
    housing_center_y = single_frame_params.housing_centers[0]
    print(f"\nHousing center Y: {housing_center_y}mm")

    # Worm is at +CD/2 from housing center, post is at -CD/2
    worm_y = housing_center_y + center_distance / 2
    post_y = housing_center_y - center_distance / 2
    print(f"Post axis Y: {post_y:.2f}mm")
    print(f"Worm axis Y: {worm_y:.2f}mm")

    # For RH tuner, worm entry is on +X side
    # The peg head after rotation has:
    # - Pip at most negative X
    # - Shaft end at most positive X
    # The cap (8mm) sits against the frame exterior at +X

    # Frame exterior at +X is at X = +box_outer/2 = +5.175mm
    frame_exterior_x = box_outer / 2

    # The cap face should sit against frame exterior
    # Cap is at... let me check the geometry more carefully
    # After rotation, what was Z=0 (shoulder/cap junction) is now at X=0
    # The shaft extends toward +X
    # The ring/pip extends toward -X

    # Actually, the peg head STEP has the shoulder at Z=0, ring at Z<0
    # After rotation by -90° around Y:
    # - Original +Z becomes +X
    # - Original -Z becomes -X
    # So shoulder (Z=0) stays at X=0
    # Ring (Z<0) goes to X<0 (toward -X)
    # Shaft (Z>0) goes to X>0 (toward +X)

    # For RH tuner (worm entry on +X), the shaft should enter from +X
    # So the shoulder (X=0 after rotation) should be at frame exterior

    # After -90° Y rotation:
    # - Pip (was Z=-19) is now at X=+19
    # - Shoulder (was Z=0) is now at X=0
    # - Worm (was Z=0 to 7.8) is now at X=0 to -7.8
    # - Shaft end (was Z=9.1) is now at X=-9.1

    # Cavity dimensions
    cavity = frame_params.box_inner  # 8.15mm
    half_cavity = cavity / 2  # 4.075mm

    # Worm must fit in cavity with 0.1mm clearance each side
    worm_length = config.peg_head.worm_length  # 7.8mm
    clearance = (cavity - worm_length) / 2  # 0.175mm

    # Position worm centered in cavity
    # Worm in local coords: X = 0 to -7.8
    # Want worm centered: X = +3.9 to -3.9 in frame coords
    # So local X=0 should be at frame X = +3.9
    # Which means: peg_x = half_cavity - clearance = 4.075 - 0.175 = 3.9

    peg_x = half_cavity - clearance

    print(f"\nPositioning peg head (worm centered in cavity):")
    print(f"  Frame exterior (+X): {frame_exterior_x:.2f}mm")
    print(f"  Frame interior (+X): {half_cavity:.2f}mm")
    print(f"  Cavity: {cavity:.2f}mm, worm: {worm_length:.2f}mm, clearance: {clearance:.2f}mm each side")
    print(f"  Peg head X offset: {peg_x:.2f}mm")
    print(f"\n  With this positioning:")
    print(f"    Worm back (shoulder) at X = {peg_x:.2f}mm")
    print(f"    Worm front at X = {peg_x - worm_length:.2f}mm")
    print(f"    Entry shaft (X=0 to +1) at X = {peg_x:.2f} to {peg_x + 1:.2f}mm")
    print(f"    Cap (X=+1 to +2) at X = {peg_x + 1:.2f} to {peg_x + 2:.2f}mm")
    print(f"    Shaft end at X = {peg_x - 9.1:.2f}mm")
    print(f"    Frame -X exterior at X = {-frame_exterior_x:.2f}mm")
    print(f"\n  Check: Is cap outside frame? Cap at {peg_x + 2:.2f}, frame exterior at {frame_exterior_x:.2f}")

    # Position peg head
    peg_positioned = peg_head.locate(Location((peg_x, worm_y, worm_z)))

    # Show components
    show_object(frame, name="Frame", options={"color": (0.8, 0.7, 0.5), "alpha": 0.5})
    show_object(peg_positioned, name="Peg_Head", options={"color": (0.9, 0.7, 0.3)})

    # Show axis markers
    worm_axis_marker = Box(20, 0.5, 0.5, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    worm_axis_marker = worm_axis_marker.locate(Location((0, worm_y, worm_z)))
    show_object(worm_axis_marker, name="Worm_Axis", options={"color": (1, 0, 0)})

    post_axis_marker = Box(0.5, 0.5, 20, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    post_axis_marker = post_axis_marker.locate(Location((0, post_y, -box_outer/2)))
    show_object(post_axis_marker, name="Post_Axis", options={"color": (0, 0, 1)})

    print("\nVisualization sent to OCP viewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
