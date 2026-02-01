"""Single tuner unit assembly.

A tuner unit consists of:
- Peg head (with integral worm)
- String post
- Worm wheel
- Retention hardware (washers, M2 screws)
"""

from pathlib import Path
from typing import Optional

from build123d import (
    Axis,
    Compound,
    Location,
    Part,
    Plane,
    Rotation,
)

from ..config.parameters import BuildConfig, Hand
from ..config.defaults import calculate_worm_z
from ..components.peg_head import create_peg_head
from ..components.string_post import create_string_post
from ..components.wheel import calculate_mesh_rotation, create_wheel_placeholder, load_wheel
from ..components.hardware import (
    create_peg_retention_washer,
    create_wheel_retention_washer,
    create_wheel_retention_screw,
    create_m2_pan_head_screw,
)


def create_tuner_unit(
    config: BuildConfig,
    wheel_step_path: Optional[Path] = None,
    worm_step_path: Optional[Path] = None,
    include_hardware: bool = True,
) -> dict[str, Part]:
    """Create a single tuner unit with all components.

    Components are positioned relative to the post axis at origin:
    - Post axis is Z (vertical)
    - Worm axis is X (horizontal), offset by center distance

    Args:
        config: Build configuration
        wheel_step_path: Optional path to wheel STEP file
        worm_step_path: Optional path to worm STEP file (for mesh rotation calculation)
        include_hardware: Whether to include washers, screws, E-clips

    Returns:
        Dictionary of component name to Part
    """
    scale = config.scale
    center_distance = config.gear.center_distance * scale

    # Frame dimensions for positioning
    frame = config.frame
    box_outer = frame.box_outer * scale
    wall = frame.wall_thickness * scale

    # String post dimensions (derived from frame and wheel)
    post_params = config.string_post
    wheel_face_width = config.gear.wheel.face_width
    dd_h = post_params.get_dd_cut_length(wheel_face_width) * scale
    bearing_h = post_params.get_bearing_length(frame.wall_thickness) * scale

    # Apply mesh rotation from config (pre-calculated for optimal tooth alignment)
    # For LH, negate rotation because mirroring changes tooth angular positions:
    # tooth at θ → tooth at (180° - θ), so optimal rotation becomes -mesh_rotation
    mesh_rotation = config.gear.mesh_rotation_deg
    if config.hand == Hand.LEFT:
        mesh_rotation = -mesh_rotation

    # String post - positioned so bearing section fills the mounting plate hole
    # Post coordinate system: Z=0 at bottom of DD section, builds upward
    # Frame coordinate system: Z=0 at mounting plate top, extends into -Z
    #
    # The bearing section (from dd_h to dd_h+bearing_h in post coords)
    # should align with the mounting plate hole (from -wall to 0 in frame coords)
    # So post Z=dd_h should align with frame Z=-wall (inside of mounting plate)
    # Therefore: post_z_offset = -wall - dd_h
    # Which means: post Z=dd_h+bearing_h aligns with frame Z=0 (top surface)
    post = create_string_post(config)
    # Rotate post DD section to match wheel bore orientation
    if mesh_rotation != 0.0:
        post = post.rotate(Axis.Z, mesh_rotation)
    post_z_offset = -(dd_h + bearing_h)
    post = post.locate(Location((0, 0, post_z_offset)))

    components = {"string_post": post}

    # Wheel - sits on the DD cut section of the post
    if wheel_step_path is not None and wheel_step_path.exists():
        wheel = load_wheel(wheel_step_path)
        # Scale if needed (STEP is at 1:1)
        if scale != 1.0:
            wheel = wheel.scale(scale)
    else:
        wheel = create_wheel_placeholder(config)

    # Mirror wheel for LH variant (creates left-hand helix per spec Section 7)
    if config.hand == Hand.LEFT:
        wheel = wheel.mirror(Plane.YZ)

    wheel_params = config.gear.wheel
    face_width = wheel_params.face_width * scale

    # Apply same mesh rotation to wheel (already calculated above)
    if mesh_rotation != 0.0:
        wheel = wheel.rotate(Axis.Z, mesh_rotation)

    # Wheel sits on post DD section
    # DD section spans from post Z=0 to Z=dd_h
    # Wheel STEP is centered at Z=0, so shift up by half face width
    wheel_z = post_z_offset + face_width / 2
    wheel = wheel.locate(Location((0, 0, wheel_z)))
    components["wheel"] = wheel

    # Peg head - worm axis is horizontal (X), offset from post by center_distance in Y
    worm_params = config.gear.worm
    worm_length = worm_params.length * scale
    peg_head = create_peg_head(
        config,
        worm_step_path=worm_step_path,
        worm_length=worm_params.length,  # Unscaled - create_peg_head handles scaling
    )

    # Worm axis Z position depends on gear configuration
    # - Cylindrical worms: centered in frame at Z = -box_outer / 2
    # - Globoid/hobbed worms: aligned with wheel center for proper meshing
    worm_z = calculate_worm_z(config)

    # After -90° Y rotation in create_peg_head:
    # - Shoulder (local Z=0) at local X=0
    # - Worm extends from local X=0 to X=-worm_length
    # - Shaft end at local X=-shaft_length
    # - Cap/pip at local X>0 (outside frame)
    #
    # Position worm centered in cavity:
    # - Cavity is ±half_inner from center (where half_inner = box_inner/2)
    # - Worm length is worm_params.length
    # - Clearance each side = (box_inner - worm_length) / 2
    # - Shoulder should be at X = half_inner - clearance
    box_inner = frame.box_inner * scale
    half_inner = box_inner / 2
    worm_clearance = (box_inner - worm_length) / 2

    # X offset: position shoulder so worm is centered in cavity
    # For RH: worm entry on +X, cap on +X, shaft exits -X
    # For LH: mirror about YZ plane (creates left-hand thread per spec Section 7)
    if config.hand == Hand.RIGHT:
        peg_x = half_inner - worm_clearance  # Shoulder at +X side
    else:
        # LH: mirror peg head about YZ plane for left-hand thread, position at -X
        peg_head = peg_head.mirror(Plane.YZ)
        peg_x = -(half_inner - worm_clearance)

    # Y offset: worm axis is offset from post axis by center_distance
    # Post is at Y=0, worm at Y=+center_distance
    peg_y = center_distance

    peg_head = peg_head.locate(Location((peg_x, peg_y, worm_z)))
    components["peg_head"] = peg_head

    if include_hardware:
        # Peg retention washer - sits on bearing shaft end
        peg_washer = create_peg_retention_washer(config)
        peg_params = config.peg_head
        shaft_length = peg_params.get_shaft_length(frame.wall_thickness) * scale
        washer_thickness = peg_params.washer_thickness * scale

        # Shaft end position:
        # After -90° Y rotation in create_peg_head, shaft extends toward -X (for RH)
        # Shoulder at peg_x, shaft end at peg_x - shaft_length
        if config.hand == Hand.RIGHT:
            shaft_end_x = peg_x - shaft_length
            # Washer sits against shaft end, body extends toward -X (outside frame)
            # -90° Y rotation: washer extends from X=0 toward X=-thickness
            peg_washer = peg_washer.rotate(Axis.Y, -90)
            washer_outer_x = shaft_end_x - washer_thickness
        else:
            shaft_end_x = peg_x + shaft_length
            # Washer sits against shaft end, body extends toward +X (outside frame)
            # +90° Y rotation: washer extends from X=0 toward X=+thickness
            peg_washer = peg_washer.rotate(Axis.Y, 90)
            washer_outer_x = shaft_end_x + washer_thickness

        peg_washer = peg_washer.locate(Location((shaft_end_x, peg_y, worm_z)))
        components["peg_washer"] = peg_washer

        # M2 screw for peg retention (threads into tap bore)
        # Screw is created with shank from Z=0 to Z=length, head from Z=length upward
        # After rotation, head should be outside washer and shank goes into tap hole
        peg_screw = create_m2_pan_head_screw(config)
        screw_length = peg_params.screw_length * scale

        if config.hand == Hand.RIGHT:
            # -90° Y rotation: shank tip at local X=0, head at local X<0
            peg_screw = peg_screw.rotate(Axis.Y, -90)
            # Head sits against washer outer face, screw extends toward -X
            screw_x = washer_outer_x + screw_length
        else:
            # +90° Y rotation: shank tip at local X=0, head at local X>0
            peg_screw = peg_screw.rotate(Axis.Y, 90)
            # Head sits against washer outer face, screw extends toward +X
            screw_x = washer_outer_x - screw_length

        peg_screw = peg_screw.locate(Location((screw_x, peg_y, worm_z)))
        components["peg_screw"] = peg_screw

        # Wheel retention hardware (M2 washer + screw from below)
        # Washer sits below the DD section bottom (at post_z_offset in frame coords)
        wheel_washer_thickness = 0.5 * scale
        wheel_washer = create_wheel_retention_washer(config)
        wheel_washer_z = post_z_offset - wheel_washer_thickness
        wheel_washer = wheel_washer.locate(Location((0, 0, wheel_washer_z)))
        components["wheel_washer"] = wheel_washer

        # M2 screw threads into tap bore from below
        # Screw is created head-up (shank Z=0 to Z=length, head Z=length to Z=length+head_h)
        # Rotate 180° X to flip: head now at bottom (lowest Z), shank extends upward
        wheel_screw = create_wheel_retention_screw(config)
        wheel_screw = wheel_screw.rotate(Axis.X, 180)
        # After 180° X rotation:
        #   - Original head bottom (Z=length) is now head top at local Z=-length
        #   - Original head top (Z=length+head_h) is now head bottom at local Z=-(length+head_h)
        #   - Shank tip still at local Z=0
        # Position so head top (local Z=-length) touches washer bottom (wheel_washer_z)
        wheel_screw_length = config.string_post.thread_length * scale
        wheel_screw_z = wheel_washer_z - (-wheel_screw_length)  # = wheel_washer_z + screw_length
        wheel_screw = wheel_screw.locate(Location((0, 0, wheel_screw_z)))
        components["wheel_screw"] = wheel_screw

    return components


def create_tuner_unit_compound(
    config: BuildConfig,
    wheel_step_path: Optional[Path] = None,
    worm_step_path: Optional[Path] = None,
    include_hardware: bool = True,
) -> Compound:
    """Create a single tuner unit as a compound shape.

    Args:
        config: Build configuration
        wheel_step_path: Optional path to wheel STEP file
        worm_step_path: Optional path to worm STEP file (for mesh rotation calculation)
        include_hardware: Whether to include washers, screws, E-clips

    Returns:
        Compound containing all tuner components
    """
    components = create_tuner_unit(config, wheel_step_path, worm_step_path, include_hardware)
    return Compound(list(components.values()))
