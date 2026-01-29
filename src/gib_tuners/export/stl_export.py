"""STL file export utilities."""

from pathlib import Path
from typing import Union

from build123d import (
    Compound,
    Mesher,
    Part,
)


def export_stl(
    shape: Union[Part, Compound],
    output_path: Path,
    tolerance: float = 0.01,
    angular_tolerance: float = 0.1,
) -> None:
    """Export a shape to STL format.

    Args:
        shape: Part or Compound to export
        output_path: Output file path (should end in .stl)
        tolerance: Linear tolerance for mesh (mm)
        angular_tolerance: Angular tolerance for mesh (radians)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use Mesher for STL export
    mesher = Mesher()
    mesher.add_shape(shape)
    mesher.write(str(output_path))
