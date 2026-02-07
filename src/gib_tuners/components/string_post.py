"""String post geometry.

The string post is a stepped shaft with (from bottom to top):
- DD cut gear interface (mates with wheel) with M2 tap bore from bottom
- Frame bearing section
- Visible post section (above frame)
- Decorative cap (top)
- String hole (cross-drilled)

Assembly: Post inserted from above, wheel slides up from below onto DD section,
M2 washer and nut thread onto the tap bore to retain wheel.
"""

from build123d import (
    Align,
    Axis,
    Cylinder,
    Location,
    Part,
    Polygon,
    fillet,
    revolve,
)

from ..config.parameters import BuildConfig
from ..features.dd_cut import create_dd_cut_shaft
from ..utils.validation import check_shape_quality


def create_string_post(config: BuildConfig) -> Part:
    """Create the string post geometry.

    The post is oriented along the Z axis with:
    - Z=0 at the bottom of the DD section (with M2 tap bore)
    - Positive Z going up toward the cap

    Args:
        config: Build configuration

    Returns:
        String post Part
    """
    params = config.string_post
    scale = config.scale

    # Scaled dimensions
    cap_d = params.cap_diameter * scale
    cap_h = params.cap_height * scale

    post_d = params.post_diameter * scale
    post_h = params.post_height * scale

    bearing_d = params.bearing_diameter * scale
    # bearing_length and dd_cut_length are derived from frame and wheel params
    wall_thickness = config.frame.wall_thickness
    wheel_face_width = config.gear.wheel.face_width
    bearing_h = params.get_bearing_length(wall_thickness) * scale
    dd_length = params.get_dd_cut_length(wheel_face_width) * scale

    # M2 tap bore: 1.6mm pilot hole diameter, thread_length deep
    tap_bore_d = 1.6 * scale  # M2 tap drill size
    tap_bore_depth = params.thread_length * scale

    string_hole_d = params.string_hole_diameter * scale
    string_hole_pos = params.string_hole_position * scale

    # Build from bottom up
    z = 0.0

    # DD cut section (mates with wheel) - starts at Z=0
    # Shaft DD is undersized by dd_shaft_clearance for a slip fit in the bore
    from dataclasses import replace as _replace
    shaft_dd = _replace(
        params.dd_cut,
        diameter=params.dd_cut.diameter - params.dd_shaft_clearance,
        across_flats=params.dd_cut.across_flats - params.dd_shaft_clearance,
    )
    dd_section = create_dd_cut_shaft(shaft_dd, dd_length, scale)
    dd_section = dd_section.locate(Location((0, 0, z)))
    z += dd_length

    # Frame bearing section
    bearing = Cylinder(
        radius=bearing_d / 2,
        height=bearing_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bearing = bearing.locate(Location((0, 0, z)))
    z += bearing_h

    # Visible post section
    post = Cylinder(
        radius=post_d / 2,
        height=post_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    post = post.locate(Location((0, 0, z)))
    z += post_h

    # Cap with rounded edges and decorative grooves
    cap = Cylinder(
        radius=cap_d / 2,
        height=cap_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cap_fillet_r = params.cap_fillet * scale
    top_edges = cap.edges().filter_by_position(Axis.Z, cap_h - 0.01, cap_h + 0.01)
    bot_edges = cap.edges().filter_by_position(Axis.Z, -0.01, 0.01)
    cap = fillet(top_edges + bot_edges, radius=cap_fillet_r)

    # Concentric V-grooves on cap top
    if params.cap_groove_count > 0:
        gw = params.cap_groove_width * scale
        gd = params.cap_groove_depth * scale
        half_w = gw / 2
        # Outermost groove: outer edge at cap_groove_outer_od/2
        outer_center = (params.cap_groove_outer_od / 2 - half_w) * scale
        min_r = 0.75 * scale
        n = params.cap_groove_count
        for i in range(n):
            # Evenly spaced from min_r to outer_center
            r = min_r + i * (outer_center - min_r) / (n - 1) if n > 1 else outer_center
            tri = Polygon([(r - half_w, 0), (r + half_w, 0), (r, -gd)], align=None)
            tri_xz = tri.rotate(Axis.X, 90)
            groove = revolve(tri_xz, axis=Axis.Z, revolution_arc=360)
            groove = groove.move(Location((0, 0, cap_h)))
            cap = cap - groove

    cap = cap.locate(Location((0, 0, z)))

    # Combine all sections
    string_post = dd_section + bearing + post + cap

    # M2 tap bore - drilled up from bottom into DD section
    tap_bore = Cylinder(
        radius=tap_bore_d / 2,
        height=tap_bore_depth + 0.1,  # Slightly deeper for clean cut
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    tap_bore = tap_bore.locate(Location((0, 0, -0.1)))
    string_post = string_post - tap_bore

    # Cross-drill string hole
    # Position is measured from frame top, which is at z = dd_length + bearing_h
    frame_top_z = dd_length + bearing_h
    hole_z = frame_top_z + string_hole_pos

    string_hole = Cylinder(
        radius=string_hole_d / 2,
        height=cap_d + 2,  # Through the post
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    string_hole = string_hole.rotate(Axis.X, 90)
    string_hole = string_hole.locate(Location((0, 0, hole_z)))
    string_post = string_post - string_hole

    # Check shape quality (warns if non-manifold edges detected)
    check_shape_quality(string_post, "string_post")

    return string_post
