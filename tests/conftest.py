"""Pytest configuration and fixtures."""

import json
from pathlib import Path

import pytest

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gib_tuners.config.defaults import create_default_config, load_gear_params
from gib_tuners.config.parameters import BuildConfig, Hand


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def gear_json_path(project_root: Path) -> Path:
    """Return path to gear JSON file."""
    return project_root / "7mm-globoid.json"


@pytest.fixture
def reference_dir(project_root: Path) -> Path:
    """Return path to reference files directory."""
    return project_root / "reference"


@pytest.fixture
def default_config() -> BuildConfig:
    """Create a default build configuration."""
    return create_default_config()


@pytest.fixture
def production_config(gear_json_path: Path) -> BuildConfig:
    """Create a production build configuration with gear JSON."""
    if gear_json_path.exists():
        return create_default_config(
            scale=1.0,
            tolerance="production",
            hand=Hand.RIGHT,
            gear_json_path=gear_json_path,
        )
    return create_default_config()


@pytest.fixture
def prototype_config(gear_json_path: Path) -> BuildConfig:
    """Create a 2x prototype configuration."""
    if gear_json_path.exists():
        return create_default_config(
            scale=2.0,
            tolerance="prototype_fdm",
            hand=Hand.RIGHT,
            gear_json_path=gear_json_path,
        )
    return create_default_config(scale=2.0, tolerance="prototype_fdm")
