"""Factory functions for creating configurations from JSON and defaults."""

import json
import math
from pathlib import Path
from dataclasses import dataclass
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

# Directory paths
CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"
REFERENCE_DIR = Path(__file__).parent.parent.parent.parent / "reference"

# Default gear parameters JSON - single source of truth for gear geometry
DEFAULT_GEAR_JSON = CONFIG_DIR / "worm_gear.json"

# Clearance for worm entry hole (allows worm to pass through frame hole)
WORM_ENTRY_CLEARANCE = 0.2  # 0.1mm per side


@dataclass
class GearConfigPaths:
    """Paths for a gear configuration."""
    json_path: Path              # worm_gear.json
    config_dir: Optional[Path]   # Config directory (None for legacy root config)
    wheel_step: Optional[Path]   # wheel.step if exists
    worm_step: Optional[Path]    # worm.step if exists


def resolve_gear_config(gear_name: Optional[str] = None) -> GearConfigPaths:
    """Resolve gear config paths from name.

    Args:
        gear_name: Config name (e.g., 'm0.5_z13') or None for default

    Returns:
        GearConfigPaths with all resolved paths

    Raises:
        FileNotFoundError if config doesn't exist
    """
    if gear_name is None:
        # Legacy: root config/worm_gear.json
        wheel_step = REFERENCE_DIR / "wheel_m0.5_z13.step"
        worm_step = REFERENCE_DIR / "worm_m0.5_z1.step"
        return GearConfigPaths(
            json_path=DEFAULT_GEAR_JSON,
            config_dir=None,
            wheel_step=wheel_step if wheel_step.exists() else None,
            worm_step=worm_step if worm_step.exists() else None,
        )

    config_dir = CONFIG_DIR / gear_name
    json_path = config_dir / "worm_gear.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Gear config not found: {json_path}")

    # Check for STEP files in config dir, fall back to reference/
    wheel_step = config_dir / "wheel.step"
    if not wheel_step.exists():
        wheel_step = REFERENCE_DIR / "wheel_m0.5_z13.step"

    worm_step = config_dir / "worm.step"
    if not worm_step.exists():
        worm_step = REFERENCE_DIR / "worm_m0.5_z1.step"

    return GearConfigPaths(
        json_path=json_path,
        config_dir=config_dir,
        wheel_step=wheel_step if wheel_step.exists() else None,
        worm_step=worm_step if worm_step.exists() else None,
    )


def list_gear_configs() -> list:
    """List available gear configurations.

    Returns:
        List of config directory names that contain worm_gear.json
    """
    configs = []
    if CONFIG_DIR.exists():
        for item in CONFIG_DIR.iterdir():
            if item.is_dir() and (item / "worm_gear.json").exists():
                configs.append(item.name)
    return sorted(configs)


def load_mesh_alignment(module: float, config_dir: Optional[Path] = None) -> dict:
    """Load mesh alignment data, checking config directory first.

    Args:
        module: Gear module in mm (e.g., 0.5)
        config_dir: Optional config directory to check first

    Returns:
        Dict with optimal_rotation_deg, tooth_pitch_deg, etc., or empty dict if not found
    """
    # Check config-specific location first
    if config_dir:
        config_mesh = config_dir / "mesh_alignment.json"
        if config_mesh.exists():
            with open(config_mesh) as f:
                return json.load(f)

    # Fall back to reference directory
    mesh_json = REFERENCE_DIR / f"mesh_alignment_m{module}.json"
    if mesh_json.exists():
        with open(mesh_json) as f:
            return json.load(f)
    return {}


def load_tuner_config(config_dir: Optional[Path]) -> dict:
    """Load tuner config overrides from tuner_config.json.

    Args:
        config_dir: Config directory containing tuner_config.json

    Returns:
        Dict with frame/string_post/peg_head overrides, or empty dict if not found
    """
    if config_dir is None:
        return {}
    config_path = config_dir / "tuner_config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}


def load_gear_params(json_path: Path, config_dir: Optional[Path] = None) -> GearParams:
    """Load gear parameters from a JSON file (e.g., config/worm_gear.json).

    Args:
        json_path: Path to the gear JSON file
        config_dir: Optional config directory for mesh alignment lookup

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

    # Load base mesh rotation from mesh_alignment JSON (wormgear optimizer output)
    # This is the optimal rotation for Z-aligned axes; will be adjusted for Z-offset in create_default_config
    module = worm_data["module_mm"]
    mesh_alignment = load_mesh_alignment(module, config_dir)
    mesh_rotation_base = mesh_alignment.get("optimal_rotation_deg", 0.0)

    return GearParams(
        worm=worm,
        wheel=wheel,
        center_distance=assembly_data["centre_distance_mm"],
        pressure_angle_deg=assembly_data["pressure_angle_deg"],
        backlash=assembly_data["backlash_mm"],
        ratio=assembly_data["ratio"],
        mesh_rotation_deg=mesh_rotation_base,
    )


def create_default_config(
    scale: float = 1.0,
    tolerance: str = "production",
    hand: Hand = Hand.RIGHT,
    gear_json_path: Optional[Path] = None,
    config_dir: Optional[Path] = None,
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
        config_dir: Optional config directory for tuner_config.json overrides

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
        gear = load_gear_params(gear_json_path, config_dir)
    else:
        # Fallback to hardcoded defaults if JSON not found
        gear = GearParams(worm=WormParams(), wheel=WheelParams())

    # Load tuner config overrides (frame, string_post, peg_head)
    tuner_overrides = load_tuner_config(config_dir)
    frame_overrides = tuner_overrides.get("frame", {})
    string_post_overrides = tuner_overrides.get("string_post", {})

    # Derive StringPostParams with dd_cut_length = wheel face width
    # Apply any overrides from tuner_config.json
    string_post_kwargs = {"dd_cut_length": gear.wheel.face_width}
    string_post_kwargs.update(string_post_overrides)
    string_post = StringPostParams(**string_post_kwargs)

    # Derive FrameParams with worm_entry_hole = worm tip diameter + clearance
    # Apply any overrides from tuner_config.json
    worm_entry_hole = gear.worm.tip_diameter + WORM_ENTRY_CLEARANCE
    frame_kwargs = {"worm_entry_hole": worm_entry_hole}
    frame_kwargs.update(frame_overrides)
    frame = FrameParams(**frame_kwargs)

    # Validate: worm must fit through entry hole
    if gear.worm.tip_diameter >= worm_entry_hole:
        raise ValueError(
            f"Worm tip diameter ({gear.worm.tip_diameter}mm) must be less than "
            f"worm entry hole ({worm_entry_hole}mm)"
        )

    # Calculate Z-offset correction for mesh rotation
    # The mesh_alignment JSON gives optimal rotation for Z-aligned axes (worm and wheel at same Z).
    # In the actual assembly, the wheel and worm are at different Z heights, so we need to correct.
    #
    # From tuner_unit.py:
    #   post_z_offset = -(dd_h + bearing_h)
    #   wheel_z = post_z_offset + face_width / 2  (wheel center)
    #   worm_z = -box_outer / 2  (worm axis)
    #   z_offset = wheel_z - worm_z
    #
    # Z offset is perpendicular to worm axis. Due to helix geometry:
    #   effective_axial_shift = z_offset × tan(lead_angle)
    #   worm_rotation = (effective_axial_shift / lead) × 360°
    #   wheel_rotation = worm_rotation / ratio
    dd_h = string_post.dd_cut_length
    bearing_h = string_post.bearing_length
    face_width = gear.wheel.face_width
    box_outer = frame.box_outer
    lead = gear.worm.lead
    ratio = gear.ratio
    lead_angle_rad = math.radians(gear.worm.lead_angle_deg)

    post_z_offset = -(dd_h + bearing_h)
    wheel_z = post_z_offset + face_width / 2
    worm_z = -box_outer / 2
    z_offset = wheel_z - worm_z

    # Convert Z offset to wheel rotation using lead angle geometry
    effective_axial_shift = z_offset * math.tan(lead_angle_rad)
    z_correction_deg = (effective_axial_shift / lead) * 360.0 / ratio

    # Apply correction to get final mesh rotation
    final_mesh_rotation = gear.mesh_rotation_deg + z_correction_deg

    # Create updated gear params with corrected rotation
    gear = GearParams(
        worm=gear.worm,
        wheel=gear.wheel,
        center_distance=gear.center_distance,
        pressure_angle_deg=gear.pressure_angle_deg,
        backlash=gear.backlash,
        extra_backlash=gear.extra_backlash,
        ratio=gear.ratio,
        mesh_rotation_deg=final_mesh_rotation,
    )

    return BuildConfig(
        scale=scale,
        tolerance=tol_config,
        hand=hand,
        gear=gear,
        frame=frame,
        string_post=string_post,
    )
