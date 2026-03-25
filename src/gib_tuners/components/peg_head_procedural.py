"""Procedural peg head geometry — no STEP file dependency.

Builds the peg head body (ring, pip, cap, shoulder, gear shaft) entirely from
parametric build123d operations.  This replaces the STEP-imported head geometry
step in peg_head.py; the worm, bearing shaft, and tap hole are added separately
by the existing peg head pipeline.

Part anatomy (top to bottom, positive Z to negative Z):
  gear shaft -> shoulder -> cap -> ringshaft -> ring -> stalk -> pip

Build approach:
- Upper body (gear shaft + shoulder + cap) as one revolve
- Ringshaft as smooth spline revolve, tangent to cap and ring
- Ring as sphere -> split -> bore -> fillet
- Stalk + pip as one revolve with pip fillets in the 2D profile
- Fuse all parts + ring outer fillets + bore-plane inner fillets

Z-axis convention: Z=0 at shoulder top (datum), positive up (gear shaft),
negative down (cap -> ringshaft -> ring -> stalk -> pip).
"""

import logging
import math
from dataclasses import dataclass

from build123d import (
    Align,
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Cylinder,
    Line,
    Part,
    Plane,
    Sphere,
    Spline,
    ThreePointArc,
    Vector,
    make_face,
    revolve,
)

from ..config.parameters import BuildConfig
from ..utils.validation import check_shape_quality

logger = logging.getLogger(__name__)

__all__ = [
    "PegHeadGeometryParams",
    "DEFAULT_GEOMETRY",
    "create_peg_head_geometry",
    "create_peg_head_procedural",
]


@dataclass(frozen=True)
class PegHeadGeometryParams:
    """Procedural peg head geometry parameters.

    All dimensions in mm.  Where possible, values match PegHeadParams
    so the procedural head is dimensionally identical to the STEP reference.
    """

    # -- Cross-section radii --
    shaft_r: float = 1.9           # gear shaft radius
    shoulder_r: float = 3.5        # wider step at shaft base
    ringshaft_r: float = 1.78      # narrow neck between cap and ring
    stalk_r: float = 0.75          # rod connecting ring to pip (dia 1.5mm)
    pip_r: float = 1.05            # locating pip radius
    bore_r: float = 4.9            # string bore through ring

    # -- Section lengths --
    shaft_length: float = 10.4     # gear shaft extends upward from datum
    shoulder_height: float = 1.2   # shoulder step below datum
    pip_height: float = 1.2        # pip cylinder height

    # -- Cap (rounded underside of shoulder, torus arc) --
    cap_r: float = 4.25            # outer radius of the cap
    cap_flat_ratio: float = 0.75   # flat radius as fraction of cap_r
    cap_depth: float = 1.0         # Z depth of the dome

    # -- Ring (sphere sliced by two near-parallel planes, bored out) --
    sphere_r: float = 6.25         # ring sphere radius
    ring_center_depth: float = 11.45  # depth from datum to sphere centre
    bore_offset: float = 0.25      # bore axis below sphere centre
    ring_half_thickness: float = 1.829  # half-thickness at string axis
    ring_taper: float = 0.0355     # slight inward taper of cut planes

    # -- Ringshaft --
    ringshaft_flare_depth: float = 2.3   # spline waypoint depth below cap
    ringshaft_overlap: float = 0.1       # overlap into cap for clean boolean
    ringshaft_ring_penetration: float = 1.0  # penetration into ring sphere

    # -- Stalk + pip placement --
    stalk_ring_penetration: float = 0.5  # stalk extends up into ring
    stalk_pip_gap: float = 0.2           # exposed gap between ring and pip

    # -- Fillets --
    ring_outer_fillet_r: float = 0.5     # fillet on ring outer edges
    pip_fillet_r: float = 0.3            # fillet on pip top and bottom

    @property
    def cap_flat_r(self) -> float:
        """Radius where the dome meets the flat cap surface."""
        return self.cap_r * self.cap_flat_ratio

    @property
    def cap_arc_start_deg(self) -> float:
        """Torus arc start angle, derived from cap geometry constraints."""
        dr = self.cap_r - self.cap_flat_r
        hyp = math.sqrt(self.cap_depth ** 2 + dr ** 2)
        return math.degrees(
            math.asin(dr / hyp) - math.atan2(self.cap_depth, dr)
        )

    @property
    def cap_minor_r(self) -> float:
        """Torus arc minor radius, derived from cap depth and start angle."""
        return self.cap_depth / (1 - math.sin(math.radians(self.cap_arc_start_deg)))

    @property
    def cap_arc_mid_deg(self) -> float:
        """Midpoint angle for three-point arc construction."""
        return (self.cap_arc_start_deg + 90) / 2


# Default geometry matching the 7mm reference peg head
DEFAULT_GEOMETRY = PegHeadGeometryParams()


def _extract_solid(shape):
    """Extract the largest solid from a boolean result."""
    if hasattr(shape, "solids") and shape.solids():
        solids = shape.solids()
        if len(solids) > 1:
            logger.warning(
                "Boolean produced %d solids; keeping largest by volume", len(solids)
            )
        return max(solids, key=lambda s: s.volume)
    return shape


def create_peg_head_geometry(
    geometry: PegHeadGeometryParams = DEFAULT_GEOMETRY,
) -> Part:
    """Build the peg head solid from parameters.

    Returns the head geometry with Z=0 at the shoulder top (datum).
    Gear shaft extends in +Z, ring/pip in -Z.

    Args:
        geometry: Procedural geometry parameters.

    Returns:
        Peg head Part (unscaled, unrotated).
    """
    g = geometry

    # -- Derived Z positions --
    shoulder_top_z = 0.0
    shoulder_bot_z = -g.shoulder_height
    shaft_top_z = g.shaft_length

    cap_bot_z = shoulder_bot_z - g.cap_depth
    cap_torus_cz = cap_bot_z + g.cap_minor_r

    sphere_cz = -g.ring_center_depth
    sphere_top_z = sphere_cz + g.sphere_r
    sphere_bot_z = sphere_cz - g.sphere_r
    bore_cz = sphere_cz - g.bore_offset

    ringshaft_top_z = cap_bot_z + g.ringshaft_overlap
    ringshaft_bot_z = sphere_top_z - g.ringshaft_ring_penetration
    ringshaft_flare_z = cap_bot_z - g.ringshaft_flare_depth

    stalk_top_z = sphere_bot_z + g.stalk_ring_penetration
    pip_top_z = sphere_bot_z - g.stalk_pip_gap
    pip_bot_z = pip_top_z - g.pip_height

    # Ring cut planes (nearly parallel, slight taper)
    n = math.sqrt(1 + g.ring_taper ** 2)
    plane1 = Plane(
        origin=(0, g.ring_half_thickness, 0),
        z_dir=(0, -1 / n, g.ring_taper / n),
    )
    plane2 = Plane(
        origin=(0, -g.ring_half_thickness, 0),
        z_dir=(0, 1 / n, g.ring_taper / n),
    )

    # ---------------------------------------------------------------
    # 1. Upper body: single revolve (gear shaft + shoulder + cap)
    # ---------------------------------------------------------------
    cap_flat_r = g.cap_flat_r
    cap_minor_r = g.cap_minor_r
    cap_arc_start_deg = g.cap_arc_start_deg
    cap_arc_mid_deg = g.cap_arc_mid_deg

    arc_start_r = cap_flat_r + cap_minor_r * math.cos(math.radians(cap_arc_start_deg))
    arc_start_z = cap_torus_cz - cap_minor_r * math.sin(math.radians(cap_arc_start_deg))
    arc_mid_r = cap_flat_r + cap_minor_r * math.cos(math.radians(cap_arc_mid_deg))
    arc_mid_z = cap_torus_cz - cap_minor_r * math.sin(math.radians(cap_arc_mid_deg))
    arc_end_r = cap_flat_r
    arc_end_z = cap_bot_z

    with BuildPart() as upper_build:
        with BuildSketch(Plane.XZ) as _sk:
            with BuildLine() as _ln:
                Line((0, shaft_top_z), (g.shaft_r, shaft_top_z))
                Line((g.shaft_r, shaft_top_z), (g.shaft_r, shoulder_top_z))
                Line((g.shaft_r, shoulder_top_z), (g.shoulder_r, shoulder_top_z))
                Line((g.shoulder_r, shoulder_top_z), (g.shoulder_r, shoulder_bot_z))
                Line((g.shoulder_r, shoulder_bot_z), (arc_start_r, arc_start_z))
                ThreePointArc(
                    (arc_start_r, arc_start_z),
                    (arc_mid_r, arc_mid_z),
                    (arc_end_r, arc_end_z),
                )
                Line((arc_end_r, arc_end_z), (0, arc_end_z))
                Line((0, arc_end_z), (0, shaft_top_z))
            make_face()
        revolve(axis=Axis.Z)
    upper_body = upper_build.part

    # ---------------------------------------------------------------
    # 2. Ring: sphere -> split -> bore
    # ---------------------------------------------------------------
    sphere = Sphere(radius=g.sphere_r).translate(Vector(0, 0, sphere_cz))
    ring_disc = sphere.split(plane1).split(plane2)
    if abs(ring_disc.volume - sphere.volume) < 1e-6:
        raise ValueError(
            "Ring split planes did not intersect sphere — check ring geometry params"
        )

    bore_cyl = Cylinder(
        radius=g.bore_r,
        height=4 * g.sphere_r,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    bore_cyl = bore_cyl.rotate(Axis.X, 90).translate(Vector(0, 0, bore_cz))
    ring = (ring_disc - bore_cyl).solids()[0]

    # ---------------------------------------------------------------
    # 3. Ringshaft: smooth spline revolve, tangent to cap and ring
    # ---------------------------------------------------------------
    r_at_sphere = math.sqrt(
        g.sphere_r ** 2 - (ringshaft_bot_z - sphere_cz) ** 2
    )
    sphere_dz = ringshaft_bot_z - sphere_cz
    sphere_tan = (sphere_dz, -r_at_sphere)
    cap_tan = (0, -1)

    with BuildPart() as ringshaft_build:
        with BuildSketch(Plane.XZ) as _sk:
            with BuildLine() as _ln:
                Spline(
                    (g.ringshaft_r, ringshaft_top_z),
                    (g.ringshaft_r, ringshaft_flare_z),
                    (r_at_sphere, ringshaft_bot_z),
                    tangents=(cap_tan, sphere_tan),
                )
                Line((r_at_sphere, ringshaft_bot_z), (0, ringshaft_bot_z))
                Line((0, ringshaft_bot_z), (0, ringshaft_top_z))
                Line((0, ringshaft_top_z), (g.ringshaft_r, ringshaft_top_z))
            make_face()
        revolve(axis=Axis.Z)
    ringshaft = ringshaft_build.part.split(plane1).split(plane2)

    # ---------------------------------------------------------------
    # 4. Stalk + pip: single revolve with pip fillets in profile
    # ---------------------------------------------------------------
    # Fillet offset at 45° — used to place the arc midpoint
    f45 = g.pip_fillet_r * (1 - math.cos(math.radians(45)))

    with BuildPart() as pip_build:
        with BuildSketch(Plane.XZ) as _sk:
            with BuildLine() as _ln:
                Line((0, stalk_top_z), (g.stalk_r, stalk_top_z))
                Line((g.stalk_r, stalk_top_z), (g.stalk_r, pip_top_z))
                if g.stalk_r < g.pip_r - g.pip_fillet_r - 1e-6:
                    Line(
                        (g.stalk_r, pip_top_z),
                        (g.pip_r - g.pip_fillet_r, pip_top_z),
                    )
                ThreePointArc(
                    (g.pip_r - g.pip_fillet_r, pip_top_z),
                    (g.pip_r - f45, pip_top_z - f45),
                    (g.pip_r, pip_top_z - g.pip_fillet_r),
                )
                Line(
                    (g.pip_r, pip_top_z - g.pip_fillet_r),
                    (g.pip_r, pip_bot_z + g.pip_fillet_r),
                )
                ThreePointArc(
                    (g.pip_r, pip_bot_z + g.pip_fillet_r),
                    (g.pip_r - f45, pip_bot_z + f45),
                    (g.pip_r - g.pip_fillet_r, pip_bot_z),
                )
                Line((g.pip_r - g.pip_fillet_r, pip_bot_z), (0, pip_bot_z))
                Line((0, pip_bot_z), (0, stalk_top_z))
            make_face()
        revolve(axis=Axis.Z)
    stalk_pip = pip_build.part

    # ---------------------------------------------------------------
    # 5. Fuse all parts + ring outer fillets
    # ---------------------------------------------------------------
    ring_assembly = ring.fuse(ringshaft)

    ring_outer_edges = []
    for edge in ring_assembly.edges():
        center = edge.center()
        d_sphere = abs(
            math.sqrt(
                center.X ** 2
                + center.Y ** 2
                + (center.Z - sphere_cz) ** 2
            )
            - g.sphere_r
        )
        if d_sphere < 0.1:
            for plane in [plane1, plane2]:
                po = Vector(plane.origin)
                pn = Vector(plane.z_dir)
                ec = Vector(center.X, center.Y, center.Z)
                if abs((ec - po).dot(pn)) < 0.01:
                    ring_outer_edges.append(edge)
                    break

    if ring_outer_edges:
        try:
            ring_assembly = ring_assembly.fillet(
                g.ring_outer_fillet_r, ring_outer_edges
            )
            if hasattr(ring_assembly, "solids") and ring_assembly.solids():
                ring_assembly = ring_assembly.solids()[0]
        except (ValueError, RuntimeError) as e:
            logger.warning("Ring outer fillet failed (non-critical): %s", e)

    solid = ring_assembly.fuse(upper_body).fuse(stalk_pip)

    # ---------------------------------------------------------------
    # 6. Bore-plane inner edge fillets
    # ---------------------------------------------------------------
    bore_edges = []
    for edge in solid.edges():
        center = edge.center()
        d_from_bore = abs(
            math.sqrt(center.X ** 2 + (center.Z - bore_cz) ** 2) - g.bore_r
        )
        if d_from_bore < 0.1:
            for plane in [plane1, plane2]:
                po = Vector(plane.origin)
                pn = Vector(plane.z_dir)
                ec = Vector(center.X, center.Y, center.Z)
                if abs((ec - po).dot(pn)) < 0.05:
                    bore_edges.append(edge)
                    break

    if bore_edges:
        try:
            solid = solid.fillet(g.ring_outer_fillet_r, bore_edges)
            solid = _extract_solid(solid)
        except (ValueError, RuntimeError) as e:
            logger.warning("Bore fillet failed (non-critical): %s", e)

    return _extract_solid(solid)


def create_peg_head_procedural(
    config: BuildConfig,
    geometry: PegHeadGeometryParams = DEFAULT_GEOMETRY,
) -> Part:
    """Create a procedurally-built peg head, matching project conventions.

    This is a drop-in alternative to `create_peg_head` for the head geometry.
    It builds the ring, pip, cap, shoulder, and gear shaft from parameters
    instead of importing a STEP file.

    The result is oriented with Z=0 at the shoulder datum:
    - Gear shaft at Z > 0
    - Ring, stalk, pip at Z < 0

    For assembly integration (worm, bearing shaft, tap hole), use this as
    input to the existing peg head pipeline.

    Args:
        config: Build configuration (scale is applied).
        geometry: Procedural geometry parameters.

    Returns:
        Peg head Part.
    """
    solid = create_peg_head_geometry(geometry)

    # Apply scale
    if config.scale != 1.0:
        solid = solid.scale(config.scale)

    check_shape_quality(solid, "peg_head_procedural")

    return solid
