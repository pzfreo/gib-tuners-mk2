"""Tolerance profiles for different manufacturing methods."""

from dataclasses import dataclass
from typing import Dict

from .parameters import ToleranceConfig


@dataclass(frozen=True)
class ToleranceProfile:
    """Named tolerance profile with description."""
    config: ToleranceConfig
    description: str


# Pre-defined tolerance profiles from spec Section 1a
TOLERANCE_PROFILES: Dict[str, ToleranceProfile] = {
    "production": ToleranceProfile(
        config=ToleranceConfig(hole_clearance=0.05, name="production"),
        description="Machined brass (final production)",
    ),
    "prototype_resin": ToleranceProfile(
        config=ToleranceConfig(hole_clearance=0.10, name="prototype_resin"),
        description="1:1 resin print validation",
    ),
    "prototype_fdm": ToleranceProfile(
        config=ToleranceConfig(hole_clearance=0.20, name="prototype_fdm"),
        description="2:1 FDM functional test",
    ),
}


def get_tolerance(name: str) -> ToleranceConfig:
    """Get a tolerance config by profile name.

    Args:
        name: Profile name ('production', 'prototype_resin', 'prototype_fdm')

    Returns:
        ToleranceConfig for the named profile

    Raises:
        KeyError: If profile name not found
    """
    if name not in TOLERANCE_PROFILES:
        available = ", ".join(TOLERANCE_PROFILES.keys())
        raise KeyError(f"Unknown tolerance profile '{name}'. Available: {available}")
    return TOLERANCE_PROFILES[name].config
