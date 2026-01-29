"""Dataclass definitions for all component parameters.

All dimensions are in millimeters. Parameters are frozen for immutability.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class Hand(Enum):
    """Handedness of the tuner assembly."""
    RIGHT = "right"
    LEFT = "left"


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
    # Box section dimensions (standard 10x10x1 until real measurements taken)
    box_outer: float = 10.0  # Outer dimension of square tube
    wall_thickness: float = 1.0  # Wall thickness

    # Housing dimensions
    housing_length: float = 16.2  # Length of each rigid box section
    end_length: float = 10.0  # Distance from frame end to housing edge (symmetric)

    # Layout
    num_housings: int = 5  # Number of tuning stations (1 to N)
    tuner_pitch: float = 27.2  # Center-to-center spacing between tuners

    # Hole diameters (nominal, before tolerance adjustment)
    post_bearing_hole: float = 4.2  # Top face, for string post shaft
    wheel_inlet_hole: float = 8.0  # Bottom face, for wheel insertion
    worm_entry_hole: float = 6.2  # Side face, for worm insertion
    peg_bearing_hole: float = 4.0  # Side face, for peg shaft bearing
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
    """Parameters for the globoid worm (integral to peg head)."""
    module: float = 0.5
    num_starts: int = 1
    pitch_diameter: float = 5.0
    tip_diameter: float = 6.0
    root_diameter: float = 3.75
    lead: float = 1.5708  # π/2
    lead_angle_deg: float = 5.71
    length: float = 7.0
    hand: Hand = Hand.RIGHT

    # Globoid-specific
    throat_reduction: float = 0.1
    throat_curvature_radius: float = 3.0


@dataclass(frozen=True)
class WheelParams:
    """Parameters for the worm wheel."""
    module: float = 0.5
    num_teeth: int = 13
    pitch_diameter: float = 6.5
    tip_diameter: float = 7.5
    root_diameter: float = 5.25
    face_width: float = 6.0
    bore: DDCutParams = DDCutParams()


@dataclass(frozen=True)
class GearParams:
    """Combined gear set parameters."""
    worm: WormParams
    wheel: WheelParams
    center_distance: float = 5.75
    pressure_angle_deg: float = 25.0
    backlash: float = 0.1
    extra_backlash: float = 0.0  # Additional backlash beyond gear design
    ratio: int = 13


@dataclass(frozen=True)
class PegHeadParams:
    """Parameters for the peg head assembly (cast with integral worm).

    Structure from outside to inside frame (RH tuner):
    - Ring (finger grip) sits outside frame
    - Cap sits against frame exterior, stops push-in
    - Entry shaft passes through worm entry hole
    - Worm threads mesh with wheel in cavity
    - Bearing shaft passes through peg bearing hole on opposite side
    """
    # Ring dimensions (finger grip)
    ring_od: float = 12.5  # Outer diameter (Onshape: headouterd)
    ring_bore: float = 9.8  # Inner bore (Onshape: headinnerd)
    ring_width: float = 7.8  # Width (flat-to-flat)
    ring_height: float = 8.0  # Overall height
    chamfer: float = 1.0  # Edge chamfer

    # Button (decorative end, outside ring)
    button_diameter: float = 8.0  # Onshape: capd (note: Onshape uses "cap" for button)
    button_height: float = 1.0  # Onshape: capl

    # Cap (sits against frame, stops push-in)
    cap_diameter: float = 8.0  # Must be > worm_entry_hole (6.2mm)
    cap_length: float = 1.0

    # Entry shaft (passes through worm entry hole)
    entry_shaft_diameter: float = 6.0  # Onshape: shoulderd - fits in 6.2mm hole
    entry_shaft_length: float = 1.2  # Onshape: shoulderl - through frame wall

    # Bearing shaft (opposite side, through peg bearing hole)
    bearing_diameter: float = 3.8  # Onshape: shankd - fits in 4.0mm hole
    bearing_length: float = 2.4  # Onshape: shanklength

    # Retention
    screw_thread: str = "M2"
    screw_length: float = 3.0
    washer_od: float = 5.0
    washer_id: float = 2.2
    washer_thickness: float = 0.5


@dataclass(frozen=True)
class StringPostParams:
    """Parameters for the string post (Swiss screw machined)."""
    # Cap (decorative top)
    cap_diameter: float = 7.5
    cap_height: float = 1.0
    cap_chamfer: float = 0.3

    # Visible post (above frame)
    post_diameter: float = 6.0
    post_height: float = 5.5

    # Frame bearing section
    bearing_diameter: float = 4.0
    bearing_length: float = 1.0  # Through frame wall

    # Wheel interface
    dd_cut: DDCutParams = DDCutParams()
    dd_cut_length: float = 6.0  # Matches wheel face width

    # M2 tap bore (drilled into bottom of DD section for screw retention)
    thread_size: str = "M2"
    tap_bore_diameter: float = 1.6  # M2 tap drill size
    thread_length: float = 4.0  # Depth of tapped hole (for 4mm M2 screw)

    # String hole
    string_hole_diameter: float = 1.5
    string_hole_position: float = 2.75  # Centered in visible post (post_height / 2)

    @property
    def total_length(self) -> float:
        """Total length from DD bottom to cap top."""
        return (
            self.cap_height +
            self.post_height +
            self.bearing_length +
            self.dd_cut_length
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
