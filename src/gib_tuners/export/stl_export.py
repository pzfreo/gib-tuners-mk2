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

    Uses build123d Mesher by default, falls back to OCP StlAPI_Writer
    for complex geometry with degenerate faces.

    Args:
        shape: Part or Compound to export
        output_path: Output file path (should end in .stl)
        tolerance: Linear tolerance for mesh (mm)
        angular_tolerance: Angular tolerance for mesh (radians)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try build123d Mesher first
        mesher = Mesher()
        mesher.add_shape(shape)
        mesher.write(str(output_path))
    except Exception:
        # Fall back to OCP direct export (more tolerant of degenerate faces)
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
        from OCP.StlAPI import StlAPI_Writer

        mesh = BRepMesh_IncrementalMesh(shape.wrapped, tolerance, False, angular_tolerance, True)
        mesh.Perform()

        writer = StlAPI_Writer()
        writer.Write(shape.wrapped, str(output_path))
