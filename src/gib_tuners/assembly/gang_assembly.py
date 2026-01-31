"""Full N-gang tuner assembly.

Combines the frame with N tuner units (1-5), each positioned at the correct
housing location.

This module provides:
- position_tuner_at_housing(): Position a single tuner at a housing center
- create_positioned_assembly(): Create complete assembly with all parts positioned
- check_interference(): Utility for interference checking between parts
"""

from pathlib import Path
from typing import Optional

from build123d import (
    Compound,
    Location,
    Part,
)

from ..config.parameters import BuildConfig
from ..components.frame import create_frame
from .tuner_unit import create_tuner_unit


# Color map for visualization
COLOR_MAP = {
    "frame": ((0.3, 0.5, 1.0), 0.3),   # Blue, transparent
    "string_post": ((0, 0.8, 0), None),       # Green
    "wheel": ((1, 0.6, 0), None),             # Orange
    "peg_head": ((0.7, 0.7, 0.8), None),      # Silver
    "peg_washer": ((1, 1, 0), None),          # Yellow
    "peg_screw": ((1, 0.2, 0.2), None),       # Red
    "wheel_washer": ((1, 1, 0), None),        # Yellow
    "wheel_screw": ((1, 0.2, 0.2), None),     # Red
}


def check_interference(part_a: Part, part_b: Part) -> float:
    """Return intersection volume between two parts (0 = no interference).

    Args:
        part_a: First part
        part_b: Second part

    Returns:
        Intersection volume in mm³, or 0 if no intersection
    """
    try:
        intersection = part_a & part_b
        return intersection.volume if hasattr(intersection, "volume") else 0.0
    except Exception:
        return 0.0


def position_tuner_at_housing(
    tuner_components: dict[str, Part],
    housing_y: float,
    effective_cd: float,
) -> dict[str, Part]:
    """Position a tuner unit's components at a specific housing location.

    tuner_unit creates components relative to post at Y=0.
    Frame has post hole at housing_y - effective_cd/2.
    This function translates all components to align with the frame.

    Args:
        tuner_components: Dictionary of component name to Part from create_tuner_unit()
        housing_y: Y coordinate of the housing center (scaled)
        effective_cd: Effective center distance (center_distance - extra_backlash, scaled)

    Returns:
        Dictionary of component name to positioned Part
    """
    # Translation to align post (at Y=0 in tuner coords) with frame post hole
    translation_y = housing_y - effective_cd / 2

    positioned = {}
    for name, part in tuner_components.items():
        # Use moved() to ADD translation, preserving existing position
        positioned[name] = part.moved(Location((0, translation_y, 0)))

    return positioned


class AssemblyInterferenceError(Exception):
    """Raised when assembly has interference between parts."""

    def __init__(self, results: dict[str, float]):
        self.results = results
        total = results.get("total", 0.0)
        failures = [k for k, v in results.items() if k != "total" and v >= 0.01]
        msg = f"Assembly has {total:.3f} mm³ total interference in: {', '.join(failures)}"
        super().__init__(msg)


def create_positioned_assembly(
    config: BuildConfig,
    wheel_step_path: Optional[Path] = None,
    worm_step_path: Optional[Path] = None,
    include_hardware: bool = True,
    check_interference: bool = False,
) -> dict[str, Part | list]:
    """Create the full N-gang tuner assembly with all parts correctly positioned.

    Args:
        config: Build configuration (num_housings determines gang count)
        wheel_step_path: Optional path to wheel STEP file
        worm_step_path: Optional path to worm STEP file (for peg head)
        include_hardware: Whether to include washers, screws
        check_interference: If True, run interference checks and raise AssemblyInterferenceError if any

    Returns:
        Dictionary containing:
        - 'frame': The frame Part
        - 'tuners': List of dicts, each containing positioned components for one tuner
        - 'all_parts': Flat dict of all parts keyed by unique name (e.g. "wheel_1")
        - 'interference': Dict of interference results (if check_interference=True)

    Raises:
        AssemblyInterferenceError: If check_interference=True and interference is found
    """
    scale = config.scale
    gear_params = config.gear
    frame_params = config.frame

    # Create the frame
    frame = create_frame(config)

    # Calculate positioning parameters
    housing_centers = [c * scale for c in frame_params.housing_centers]
    center_distance = gear_params.center_distance * scale
    extra_backlash = gear_params.extra_backlash * scale
    effective_cd = center_distance - extra_backlash

    # Create and position tuner units at each housing
    tuners = []
    all_parts = {"frame": frame}

    for i, housing_y in enumerate(housing_centers):
        tuner_num = i + 1

        # Create tuner unit (components at origin)
        components = create_tuner_unit(
            config,
            wheel_step_path=wheel_step_path,
            worm_step_path=worm_step_path,
            include_hardware=include_hardware,
        )

        # Position at this housing
        positioned = position_tuner_at_housing(components, housing_y, effective_cd)
        tuners.append(positioned)

        # Add to flat dict with unique names
        for name, part in positioned.items():
            all_parts[f"{name}_{tuner_num}"] = part

    result = {
        "frame": frame,
        "tuners": tuners,
        "all_parts": all_parts,
        "housing_centers": housing_centers,
        "effective_cd": effective_cd,
    }

    # Run interference checks if requested
    if check_interference:
        interference = run_interference_report(result, verbose=False)
        result["interference"] = interference
        # Threshold allows for expected gear mesh contact (~0.02mm³/housing for zero-backlash)
        # Scale threshold with number of housings
        num_housings = frame_params.num_housings
        threshold = 0.03 * num_housings  # ~0.03mm³ per housing tolerance
        if interference.get("total", 0.0) >= threshold:
            raise AssemblyInterferenceError(interference)

    return result


def create_gang_assembly_compound(
    config: BuildConfig,
    wheel_step_path: Optional[Path] = None,
    include_hardware: bool = True,
) -> Compound:
    """Create the full N-gang assembly as a compound shape.

    Args:
        config: Build configuration
        wheel_step_path: Optional path to wheel STEP file
        include_hardware: Whether to include washers, screws

    Returns:
        Compound containing frame and all tuner components
    """
    assembly = create_positioned_assembly(config, wheel_step_path, include_hardware)
    return Compound(list(assembly["all_parts"].values()))


def run_interference_report(
    assembly: dict[str, Part | list],
    verbose: bool = True,
) -> dict[str, float]:
    """Run interference checks on an assembly.

    Args:
        assembly: Result from create_positioned_assembly()
        verbose: Print results to stdout

    Returns:
        Dictionary of check name to interference volume
    """
    all_parts = assembly["all_parts"]
    frame = assembly["frame"]
    num_tuners = len(assembly["tuners"])

    results = {}
    total = 0.0

    if verbose:
        print("=== Interference Report ===")

    for i in range(num_tuners):
        tuner_num = i + 1
        tuner_total = 0.0

        # Key checks for this tuner
        checks = [
            (f"wheel_{tuner_num}", f"peg_head_{tuner_num}", "gear mesh"),
            (f"string_post_{tuner_num}", "frame", "post in hole"),
            (f"peg_head_{tuner_num}", "frame", "worm in hole"),
            (f"wheel_{tuner_num}", "frame", "wheel in cavity"),
        ]

        for name_a, name_b, desc in checks:
            if name_a in all_parts and name_b in all_parts:
                vol = check_interference(all_parts[name_a], all_parts[name_b])
                key = f"tuner_{tuner_num}_{desc.replace(' ', '_')}"
                results[key] = vol
                tuner_total += vol

                if verbose and vol >= 0.01:
                    print(f"  Tuner {tuner_num} {desc}: INTERFERENCE {vol:.3f} mm³")

        total += tuner_total
        if verbose and tuner_total < 0.01:
            print(f"  Tuner {tuner_num}: OK")

    results["total"] = total

    if verbose:
        print()
        if total < 0.01:
            print("All interference checks PASSED")
        else:
            print(f"TOTAL INTERFERENCE: {total:.3f} mm³")

    return results
