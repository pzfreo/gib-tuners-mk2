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
    diameter: float = 3.0  # Nominal shaft/bore diameter
    flat_depth: float = 0.6  # Depth of each flat
    across_flats: float = 1.8  # Distance between flats


@dataclass(frozen=True)
class FrameParams:
    """Parameters for the 5-gang frame."""
    # Box section dimensions (as manufactured)
    box_outer: float = 10.35  # Outer dimension of square tube
    wall_thickness: float = 1.1  # Wall thickness

    # Overall dimensions
    total_length: float = 145.0  # Frame length
    housing_length: float = 16.2  # Length of each rigid box section
    end_length: float = 10.0  # Distance from frame end to first/last housing center

    # Layout
    num_housings: int = 5
    tuner_pitch: float = 27.2  # Center-to-center spacing

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
    def housing_centers(self) -> Tuple[float, ...]:
        """Y positions of housing centers from frame start."""
        first_center = self.end_length + self.housing_length / 2  # 10 + 8.1 = 18.1...
        # Actually from spec: first center is at 15.1mm
        # Let me recalculate: end_length is to first housing center
        # So first center = end_length + (housing_length/2) would be wrong
        # Spec says: Housing 1 center at 15.1mm, end_length = 10.0mm
        # This means housing_length/2 = 5.1mm for end calculation...
        # Actually looking at spec more carefully:
        # end_length (10.0mm) is from frame end to first housing CENTER
        # So first center = end_length = 10.0mm... no that's not 15.1mm either
        # Let me check: 15.1 - 10.0 = 5.1mm discrepancy
        # The spec table shows first housing center at 15.1mm
        # So end_length must be measured differently
        # Actually the first center position from the spec is the source of truth
        first_center = 15.1
        return tuple(first_center + i * self.tuner_pitch for i in range(self.num_housings))

    @property
    def mounting_hole_positions(self) -> Tuple[float, ...]:
        """Y positions of mounting holes from frame start."""
        # From spec: 4.5, 31.7, 58.9, 86.1, 113.3, 140.5
        return (4.5, 31.7, 58.9, 86.1, 113.3, 140.5)


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
    num_teeth: int = 12
    pitch_diameter: float = 6.0
    tip_diameter: float = 7.0
    root_diameter: float = 4.75
    face_width: float = 6.0
    bore: DDCutParams = DDCutParams()


@dataclass(frozen=True)
class GearParams:
    """Combined gear set parameters."""
    worm: WormParams
    wheel: WheelParams
    center_distance: float = 5.5
    pressure_angle_deg: float = 25.0
    backlash: float = 0.1
    ratio: int = 12


@dataclass(frozen=True)
class PegHeadParams:
    """Parameters for the peg head assembly (cast with integral worm)."""
    # Ring dimensions
    ring_od: float = 12.8  # Outer diameter
    ring_bore: float = 9.5  # Inner bore (hollow)
    ring_width: float = 7.8  # Width (flat-to-flat)
    ring_height: float = 8.0  # Overall height
    chamfer: float = 1.0  # Edge chamfer

    # Button
    button_diameter: float = 6.0  # Decorative end button
    button_height: float = 3.5

    # Shaft sections
    shoulder_diameter: float = 8.0  # Stops pull-in through entry hole
    shoulder_length: float = 2.0
    bearing_diameter: float = 3.8  # Runs in peg bearing hole
    bearing_length: float = 1.0  # Through wall thickness

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

    # E-clip retention section
    eclip_shaft_diameter: float = 2.5
    eclip_shaft_length: float = 3.0
    eclip_groove_diameter: float = 2.1
    eclip_groove_width: float = 0.4
    eclip_od: float = 6.0  # DIN 6799 M2.5

    # String hole
    string_hole_diameter: float = 1.5
    string_hole_position: float = 4.0  # From frame top

    @property
    def total_length(self) -> float:
        """Total length from cap to shaft end."""
        return (
            self.cap_height +
            self.post_height +
            self.bearing_length +
            self.dd_cut_length +
            self.eclip_shaft_length
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
