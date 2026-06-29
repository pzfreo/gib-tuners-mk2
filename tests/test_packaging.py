"""Packaging regression tests for issue #99.

When ``gib-tuners`` is installed as a wheel (rather than run from a source
checkout) the gear-config and reference data must still be locatable. These
tests guard both the path-resolution logic and the wheel contents so the
"FileNotFoundError: Gear config 'c13-10' not found. Available:" regression
cannot return.
"""
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from gib_tuners.config import defaults
from gib_tuners.config.defaults import list_gear_configs, resolve_gear_config

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files the package loads at runtime and therefore must ship in the wheel.
REQUIRED_WHEEL_DATA = [
    "gib_tuners/data/config/c13-10/worm_gear.json",
    "gib_tuners/data/config/c13-10/tuner_config.json",
    "gib_tuners/data/config/c13-10/geometry_analysis_m0.5.json",
    "gib_tuners/data/config/c13-10/wheel_m0.5_z13.step",
    "gib_tuners/data/config/c13-10/worm_m0.5_z1.step",
    "gib_tuners/data/reference/peghead7mm.step",
    "gib_tuners/data/reference/worm_m0.5_z1.step",
]


def test_checkout_resolves_c13_10():
    """From a source checkout the production profile is discoverable."""
    assert "c13-10" in list_gear_configs()
    paths = resolve_gear_config("c13-10")
    assert paths.json_path.exists()
    assert paths.wheel_step is not None and paths.wheel_step.exists()
    assert paths.worm_step is not None and paths.worm_step.exists()


def test_env_override_takes_precedence(tmp_path, monkeypatch):
    """GIB_TUNERS_DATA_DIR redirects resolution to an arbitrary location."""
    (tmp_path / "config").mkdir()
    (tmp_path / "reference").mkdir()
    monkeypatch.setenv("GIB_TUNERS_DATA_DIR", str(tmp_path))
    assert defaults._resolve_data_dir("config") == tmp_path / "config"
    assert defaults._resolve_data_dir("reference") == tmp_path / "reference"


@pytest.mark.skipif(
    shutil.which("uv") is None, reason="uv not available to build the wheel"
)
def test_wheel_ships_runtime_data(tmp_path):
    """The built wheel must contain every runtime data file (regression for #99)."""
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1, f"expected one wheel, got {wheels}"
    names = set(zipfile.ZipFile(wheels[0]).namelist())
    missing = [f for f in REQUIRED_WHEEL_DATA if f not in names]
    assert not missing, f"wheel is missing runtime data: {missing}"
