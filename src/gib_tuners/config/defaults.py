"""Factory functions for creating configurations from JSON and defaults."""

import json
from pathlib import Path
from typing import Optional

from .parameters import (
    BuildConfig,
    DDCutParams,
    FrameParams,
    GearParams,
    Hand,
    StringPostParams,
    ToleranceConfig,
    WheelParams,
    WormParams,
)
from .tolerances import get_tolerance

# Default gear parameters JSON - single source of truth for gear geometry
DEFAULT_GEAR_JSON = Path(__file__).parent.parent.parent.parent / "config" / "worm_gear.json"
# Assembly-specific config (mesh rotation, etc.) - separate from generated gear JSON
DEFAULT_ASSEMBLY_JSON = Path(__file__).parent.parent.parent.parent / "config" / "assembly.json"

# Clearance for worm entry hole (allows worm to pass through frame hole)
WORM_ENTRY_CLEARANCE = 0.2  # 0.1mm per side


def load_gear_params(json_path: Path) -> GearParams:
    """Load gear parameters from a JSON file (e.g., config/worm_gear.json).

    Args:
        json_path: Path to the gear JSON file

    Returns:
        GearParams populated from JSON
    """
    with open(json_path) as f:
        data = json.load(f)

    worm_data = data["worm"]
    wheel_data = data["wheel"]
    assembly_data = data["assembly"]
    features_data = data.get("features", {})
    manufacturing_data = data.get("manufacturing", {})

    # Parse worm parameters
    worm = WormParams(
        module=worm_data["module_mm"],
        num_starts=worm_data["num_starts"],
        pitch_diameter=worm_data["pitch_diameter_mm"],
        tip_diameter=worm_data["tip_diameter_mm"],
        root_diameter=worm_data["root_diameter_mm"],
        lead=worm_data["lead_mm"],
        lead_angle_deg=worm_data["lead_angle_deg"],
        length=manufacturing_data.get("worm_length_mm", 7.0),
        hand=Hand.RIGHT if worm_data.get("hand", "right") == "right" else Hand.LEFT,
        throat_reduction=worm_data.get("throat_reduction_mm", 0.1),
        throat_curvature_radius=worm_data.get("throat_curvature_radius_mm", 3.0),
    )

    # Parse wheel bore (DD cut) - updated for 7.5mm wheel
    wheel_features = features_data.get("wheel", {})
    bore_diameter = wheel_features.get("bore_diameter_mm", 3.5)
    # Calculate DD parameters: flat_depth ~14% of diameter, across_flats = diameter - 2*flat_depth
    flat_depth = round(bore_diameter * 0.14, 1)  # ~0.5mm for 3.5mm bore
    across_flats = round(bore_diameter - 2 * flat_depth, 1)  # ~2.5mm for 3.5mm bore
    wheel_bore = DDCutParams(
        diameter=bore_diameter,
        flat_depth=flat_depth,
        across_flats=across_flats,
    )

    # Parse wheel parameters
    wheel = WheelParams(
        module=wheel_data["module_mm"],
        num_teeth=wheel_data["num_teeth"],
        pitch_diameter=wheel_data["pitch_diameter_mm"],
        tip_diameter=wheel_data["tip_diameter_mm"],
        root_diameter=wheel_data["root_diameter_mm"],
        face_width=manufacturing_data.get("wheel_width_mm", 6.0),
        bore=wheel_bore,
    )

    # Load mesh rotation from separate assembly config (not part of gear generator output)
    mesh_rotation = 0.0
    if DEFAULT_ASSEMBLY_JSON.exists():
        with open(DEFAULT_ASSEMBLY_JSON) as f:
            assembly_config = json.load(f)
            mesh_rotation = assembly_config.get("mesh_rotation_deg", 0.0)

    return GearParams(
        worm=worm,
        wheel=wheel,
        center_distance=assembly_data["centre_distance_mm"],
        pressure_angle_deg=assembly_data["pressure_angle_deg"],
        backlash=assembly_data["backlash_mm"],
        ratio=assembly_data["ratio"],
        mesh_rotation_deg=mesh_rotation,
    )


def create_default_config(
    scale: float = 1.0,
    tolerance: str = "production",
    hand: Hand = Hand.RIGHT,
    gear_json_path: Optional[Path] = None,
) -> BuildConfig:
    """Create a BuildConfig with defaults and optional overrides.

    Derives dependent parameters from gear config:
    - dd_cut_length = wheel.face_width (they are the same)
    - worm_entry_hole = worm.tip_diameter + clearance

    Args:
        scale: Geometry scale factor (1.0 for production, 2.0 for FDM prototype)
        tolerance: Tolerance profile name
        hand: LEFT or RIGHT hand variant
        gear_json_path: Optional path to gear JSON file (defaults to config/worm_gear.json)

    Returns:
        Configured BuildConfig instance

    Raises:
        ValueError: If worm tip diameter exceeds entry hole size
    """
    tol_config = get_tolerance(tolerance)

    # Load gear params from JSON (use default if not specified)
    if gear_json_path is None:
        gear_json_path = DEFAULT_GEAR_JSON

    if gear_json_path.exists():
        gear = load_gear_params(gear_json_path)
    else:
        # Fallback to hardcoded defaults if JSON not found
        gear = GearParams(worm=WormParams(), wheel=WheelParams())

    # Derive StringPostParams with dd_cut_length = wheel face width
    string_post = StringPostParams(
        dd_cut_length=gear.wheel.face_width,
    )

    # Derive FrameParams with worm_entry_hole = worm tip diameter + clearance
    worm_entry_hole = gear.worm.tip_diameter + WORM_ENTRY_CLEARANCE
    frame = FrameParams(
        worm_entry_hole=worm_entry_hole,
    )

    # Validate: worm must fit through entry hole
    if gear.worm.tip_diameter >= worm_entry_hole:
        raise ValueError(
            f"Worm tip diameter ({gear.worm.tip_diameter}mm) must be less than "
            f"worm entry hole ({worm_entry_hole}mm)"
        )

    return BuildConfig(
        scale=scale,
        tolerance=tol_config,
        hand=hand,
        gear=gear,
        frame=frame,
        string_post=string_post,
    )
