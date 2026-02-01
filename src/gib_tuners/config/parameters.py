"""Dataclass definitions for all component parameters.

All dimensions are in millimeters. Parameters are frozen for immutability.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class Hand(Enum):
    """Handedness of the tuner assembly."""
    RIGHT = "right"
    LEFT = "left"


class WormType(Enum):
    """Worm geometry type."""
    CYLINDRICAL = "cylindrical"
    GLOBOID = "globoid"


class WormZMode(Enum):
    """Worm Z-positioning mode override."""
    AUTO = "auto"        # Auto-detect from worm type and virtual_hobbing
    CENTERED = "centered"  # Force centered in frame (default for cylindrical)
    ALIGNED = "aligned"   # Force aligned with wheel (required for globoid)


@dataclass(frozen=True)
class ToleranceConfig:
    """Tolerance adjustments for different manufacturing methods."""
    hole_clearance: float  # Added to nominal hole diameters
    name: str


@dataclass(frozen=True)
class DDCutParams:
    """Double-D cut parameters for anti-rotation interface."""
    diameter: float = 3.5  # Nominal shaft/bore diameter
    flat_depth: float = 0.5  # Depth of each flat (14% of diameter)
    across_flats: float = 2.5  # Distance between flats


@dataclass(frozen=True)
class FrameParams:
    """Parameters for an N-gang frame (1 to N tuning stations)."""
    # Box section dimensions (measured: 10x10 outer, 7.8x7.8 inner)
    box_outer: float = 10.0  # Outer dimension of square tube
    wall_thickness: float = 1.1  # Wall thickness (measured)

    # Housing dimensions
    housing_length: float = 16.2  # Length of each rigid box section
    end_length: float = 10.0  # Distance from frame end to housing edge (symmetric)

    # Layout
    num_housings: int = 5  # Number of tuning stations (1 to N)
    tuner_pitch: float = 27.2  # Center-to-center spacing between tuners

    # Hole diameters (nominal, before tolerance adjustment)
    # Bearing holes use 0.05mm clearance (can be reamed at assembly if needed)
    post_bearing_hole: float = 4.05  # Top face, for string post shaft (4.0mm)
    wheel_inlet_hole: float = 8.0  # Bottom face, for wheel insertion
    worm_entry_hole: float = 7.2  # Side face, for worm insertion (> 7mm worm tip)
    peg_bearing_hole: float = 4.05  # Side face, for peg shaft bearing (4.0mm)
    mounting_hole: float = 3.0  # Bottom plate, for headstock bolts

    @property
    def box_inner(self) -> float:
        """Internal cavity dimension."""
        return self.box_outer - 2 * self.wall_thickness

    @property
    def total_length(self) -> float:
        """Total frame length, computed from num_housings and pitch.

        Formula: 2 * end_length + housing_length + (num_housings - 1) * pitch
        For 5 housings: 2 * 10 + 16.2 + 4 * 27.2 = 145.0mm
        """
        return (
            2 * self.end_length
            + self.housing_length
            + (self.num_housings - 1) * self.tuner_pitch
        )

    @property
    def housing_centers(self) -> Tuple[float, ...]:
        """Y positions of housing centers from frame start.

        First center = end_length + housing_length / 2 = 10 + 8.1 = 18.1mm
        """
        first_center = self.end_length + self.housing_length / 2
        return tuple(first_center + i * self.tuner_pitch for i in range(self.num_housings))

    @property
    def mounting_hole_positions(self) -> Tuple[float, ...]:
        """Y positions of mounting holes from frame start.

        Holes are centered in the gaps between housings.
        There are num_housings + 1 holes (one before first, one between each pair,
        one after last).
        """
        centers = self.housing_centers
        half_housing = self.housing_length / 2
        positions = []

        # Hole before first housing (centered in end gap)
        positions.append(self.end_length / 2)

        # Holes between housings
        for i in range(len(centers) - 1):
            gap_start = centers[i] + half_housing
            gap_end = centers[i + 1] - half_housing
            positions.append((gap_start + gap_end) / 2)

        # Hole after last housing (centered in end gap)
        positions.append(self.total_length - self.end_length / 2)

        return tuple(positions)


@dataclass(frozen=True)
class WormParams:
    """Parameters for the worm (integral to peg head)."""
    # Defaults match "balanced" config (M0.6, 10:1)
    module: float = 0.6
    num_starts: int = 1
    pitch_diameter: float = 5.8
    tip_diameter: float = 7.0
    root_diameter: float = 4.3
    lead: float = 1.885  # π × module
    lead_angle_deg: float = 5.91
    length: float = 7.8  # From manufacturing config
    hand: Hand = Hand.RIGHT
    worm_type: WormType = WormType.CYLINDRICAL

    # Globoid-specific
    throat_reduction: float = 0.1
    throat_curvature_radius: float = 3.0


@dataclass(frozen=True)
class WheelParams:
    """Parameters for the worm wheel."""
    # Defaults match "balanced" config (M0.6, 10T)
    module: float = 0.6
    num_teeth: int = 10
    pitch_diameter: float = 6.0
    tip_diameter: float = 7.2
    root_diameter: float = 4.5
    face_width: float = 7.6  # From manufacturing config
    bore: DDCutParams = DDCutParams(diameter=3.25, flat_depth=0.45, across_flats=2.35)


@dataclass(frozen=True)
class GearParams:
    """Combined gear set parameters."""
    # Defaults match "balanced" config (M0.6, 10:1)
    worm: WormParams
    wheel: WheelParams
    center_distance: float = 5.9
    pressure_angle_deg: float = 20.0
    backlash: float = 0.0
    extra_backlash: float = 0.0  # Additional backlash beyond gear design
    ratio: int = 10
    mesh_rotation_deg: float = 0.0  # Wheel rotation for optimal mesh alignment
    virtual_hobbing: bool = False  # If true, auto-aligns worm with wheel center
    worm_z_mode: WormZMode = WormZMode.AUTO  # Override worm Z positioning


@dataclass(frozen=True)
class PegHeadParams:
    """Parameters for the peg head assembly (combined from STEP files).

    Structure (from head toward bearing end):
    - Head: decorative ring with finger grip (from STEP)
    - Cap: sits outside frame, prevents push-in (8.5mm, from STEP)
    - Shoulder: fits inside worm entry hole with clearance (7mm, from STEP)
    - Worm: threaded section, merged from worm STEP
    - Shaft: bearing end, generated by code (3.5mm)
    - M2 tap hole: 4mm deep from shaft end (extends into worm)

    Construction:
    1. Import peg head STEP (ring, pip, cap, shoulder), cut at Z=0
    2. Add new shaft (fits inside worm root)
    3. Add worm STEP at Z=0 (butted against shoulder)
    4. Add M2 tap hole at shaft end

    Shaft structure (from shoulder toward bearing):
    - Worm: from gear config manufacturing.worm_length_mm
    - Gap: 0.2mm to frame cavity end
    - Bearing wall: 1.1mm (matches frame wall_thickness)
    - Extension: 0.1mm beyond frame for washer
    """
    # Ring dimensions (from peg head STEP)
    ring_od: float = 12.5  # Outer diameter (headouterd)
    ring_bore: float = 9.8  # Inner bore diameter (headinnerd) - finger grip
    ring_width_top: float = 2.4  # Width at outer edge (headthicknessattop)
    bore_offset: float = 0.25  # Bore center offset (headinneroffset)
    chamfer: float = 0.3  # Edge chamfer (smoothedges)

    # Pip (small decorative button on outside of ring)
    pip_diameter: float = 2.1  # Onshape: pipd
    pip_length: float = 1.2  # Onshape: pipl
    pip_stalk_diameter: float = 1.0  # Onshape: pipstalkd
    pip_stalk_length: float = 0.2  # Onshape: pipstalkl

    # Join (shaft through ring bore) - from peg head STEP
    join_diameter: float = 3.5  # Onshape: headjoind
    join_length: float = 3.0  # Onshape: headjoinl

    # Cap (flange against frame) - from peg head STEP
    cap_diameter: float = 8.5  # Must be > worm_entry_hole (7.2mm)
    cap_length: float = 1.0

    # Shoulder (fits in worm entry hole) - from peg head STEP
    shoulder_diameter: float = 7.0  # Must be < worm_entry_hole with clearance

    # Shaft (new, added programmatically)
    shaft_diameter: float = 4.0  # Bearing section diameter
    worm_length: float = 7.8  # From gear config manufacturing.worm_length_mm
    # Axial play for free rotation (gap between cap and frame)
    peg_bearing_axial_play: float = 0.2
    washer_clearance: float = 0.1  # Extension beyond frame

    def get_bearing_wall(self, wall_thickness: float) -> float:
        """Bearing section length = wall + axial play."""
        return wall_thickness + self.peg_bearing_axial_play

    # M2 tap hole
    tap_drill: float = 1.6  # M2 tap drill diameter
    tap_depth: float = 4.0  # Depth of tapped hole

    # Retention hardware (M2 screw with M2.5 washer for better retention)
    screw_thread: str = "M2"
    screw_length: float = 4.0  # M2 screw length (threads into tap bore)
    screw_head_diameter: float = 3.75  # M2 pan head OD (measured)
    screw_head_depth: float = 1.0  # M2 pan head height (measured)
    washer_od: float = 5.5  # M2.5 washer OD (larger for better frame overlap)
    washer_id: float = 2.7  # M2.5 washer ID (M2 screw head still captures it)
    washer_thickness: float = 0.5  # M2.5 washer thickness

    def get_shaft_length(self, wall_thickness: float) -> float:
        """Total shaft length from shoulder to end.

        Note: No explicit shaft_gap is needed because the worm is centered
        in the cavity, which provides clearance on both sides.
        Protrusion beyond frame = peg_bearing_axial_play.
        """
        return (
            self.worm_length +
            self.get_bearing_wall(wall_thickness)
        )


@dataclass(frozen=True)
class StringPostParams:
    """Parameters for the string post (Swiss screw machined).

    Note: bearing_length and dd_cut_length are DERIVED values:
    - bearing_length = wall_thickness + post_bearing_axial_play
    - dd_cut_length = wheel.face_width - dd_cut_clearance
    Use get_bearing_length() and get_dd_cut_length() methods.
    """
    # Cap (decorative top)
    cap_diameter: float = 7.5
    cap_height: float = 1.0
    cap_chamfer: float = 0.3

    # Visible post (above frame)
    post_diameter: float = 6.0
    post_height: float = 5.5

    # Frame bearing section
    bearing_diameter: float = 4.0
    # Axial play for free rotation (see spec.md Section 5a)
    # This gap allows the post+wheel assembly to rotate freely in the frame
    post_bearing_axial_play: float = 0.2

    # Wheel interface (matches balanced wheel bore)
    dd_cut: DDCutParams = DDCutParams(diameter=3.25, flat_depth=0.45, across_flats=2.35)
    # Clearance ensures screw clamps wheel to shoulder (DD doesn't bottom out in wheel bore)
    dd_cut_clearance: float = 0.1

    # M2 tap bore (drilled into bottom of DD section for screw retention)
    thread_size: str = "M2"
    tap_bore_diameter: float = 1.6  # M2 tap drill size
    thread_length: float = 4.0  # Depth of tapped hole (for 4mm M2 screw)

    # String hole
    string_hole_diameter: float = 1.5
    string_hole_position: float = 2.75  # Centered in visible post (post_height / 2)

    def get_bearing_length(self, wall_thickness: float) -> float:
        """Bearing length = wall + axial play.

        The bearing section passes through the frame wall and protrudes
        into the cavity by axial_play amount. This creates the gap that
        allows free rotation.
        """
        return wall_thickness + self.post_bearing_axial_play

    def get_dd_cut_length(self, wheel_face_width: float) -> float:
        """DD cut is slightly shorter than wheel to ensure screw clamps wheel to shoulder."""
        return wheel_face_width - self.dd_cut_clearance

    def get_total_length(self, wall_thickness: float, wheel_face_width: float) -> float:
        """Total length from DD bottom to cap top."""
        return (
            self.cap_height +
            self.post_height +
            self.get_bearing_length(wall_thickness) +
            self.get_dd_cut_length(wheel_face_width)
        )


@dataclass(frozen=True)
class BuildConfig:
    """Top-level build configuration."""
    scale: float = 1.0
    tolerance: ToleranceConfig = ToleranceConfig(hole_clearance=0.05, name="production")
    hand: Hand = Hand.RIGHT

    # Component parameters
    frame: FrameParams = FrameParams()
    gear: GearParams = GearParams(
        worm=WormParams(),
        wheel=WheelParams()
    )
    peg_head: PegHeadParams = PegHeadParams()
    string_post: StringPostParams = StringPostParams()

    def scaled(self, value: float) -> float:
        """Apply scale factor to a dimension."""
        return value * self.scale

    def with_tolerance(self, hole_diameter: float) -> float:
        """Apply tolerance to a hole diameter."""
        return hole_diameter + self.tolerance.hole_clearance
