"""Mesh analysis utilities for STL quality and wall thickness checks."""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class MeshQuality:
    """Mesh quality metrics."""
    vertices: int
    faces: int
    non_manifold_edges: int
    is_watertight: bool
    volume: float  # mm³


@dataclass
class WallThicknessResult:
    """Result of wall thickness analysis at a specific position."""
    position: float  # mm (along axis)
    inner_radius: float  # mm (hole surface)
    outer_radius: float  # mm (outer surface / root)
    wall_thickness: float  # mm
    region: str  # 'shaft', 'worm', etc.


@dataclass
class WallAnalysis:
    """Complete wall thickness analysis results."""
    min_wall: float  # mm
    min_wall_position: float  # mm
    measurements: list[WallThicknessResult]


def load_and_repair_mesh(stl_path: Path) -> "trimesh.Trimesh":
    """Load STL and repair if needed using pymeshfix.

    Args:
        stl_path: Path to STL file

    Returns:
        Repaired trimesh object
    """
    import trimesh

    mesh = trimesh.load(stl_path)

    if mesh.is_watertight:
        return mesh

    # Try pymeshfix repair
    try:
        import pymeshfix
        mf = pymeshfix.MeshFix(mesh.vertices, mesh.faces)
        mf.repair()
        mesh = trimesh.Trimesh(mf.points, mf.faces)
    except ImportError:
        pass  # pymeshfix not available
    except Exception:
        pass  # Repair failed

    return mesh


def check_mesh_quality(mesh: "trimesh.Trimesh") -> MeshQuality:
    """Check mesh quality metrics.

    Args:
        mesh: trimesh object

    Returns:
        MeshQuality dataclass with metrics
    """
    from collections import Counter

    edge_counts = Counter(tuple(sorted(e)) for e in mesh.edges)
    nme = sum(1 for c in edge_counts.values() if c != 2)

    return MeshQuality(
        vertices=len(mesh.vertices),
        faces=len(mesh.faces),
        non_manifold_edges=nme,
        is_watertight=mesh.is_watertight,
        volume=float(mesh.volume) if mesh.is_watertight else 0.0,
    )


def analyze_axial_wall_thickness(
    mesh: "trimesh.Trimesh",
    axis: int = 0,  # 0=X, 1=Y, 2=Z
    hole_radius: float = 0.8,  # mm
    sample_step: float = 0.2,  # mm
    axis_range: Optional[tuple[float, float]] = None,
) -> WallAnalysis:
    """Analyze wall thickness around an axial hole using cross-sections.

    Finds the minimum wall between an inner hole surface and outer surface
    along the specified axis.

    Args:
        mesh: trimesh object
        axis: Axis along which the hole runs (0=X, 1=Y, 2=Z)
        hole_radius: Expected radius of the hole (mm)
        sample_step: Step size for sampling along axis (mm)
        axis_range: Optional (min, max) range to analyze

    Returns:
        WallAnalysis with measurements and minimum wall
    """
    verts = mesh.vertices
    axis_vals = verts[:, axis]

    # Determine range to analyze
    if axis_range is None:
        axis_min, axis_max = axis_vals.min(), axis_vals.max()
    else:
        axis_min, axis_max = axis_range

    # Create plane normal for cross-sections
    plane_normal = [0.0, 0.0, 0.0]
    plane_normal[axis] = 1.0

    # Radial axes (perpendicular to main axis)
    radial_axes = [i for i in range(3) if i != axis]

    measurements = []
    min_wall = float('inf')
    min_wall_pos = 0.0

    for pos in np.arange(axis_min, axis_max, sample_step):
        # Try cross-section first for accuracy
        plane_origin = [0.0, 0.0, 0.0]
        plane_origin[axis] = pos

        try:
            section = mesh.section(plane_origin=plane_origin, plane_normal=plane_normal)
            if section is not None:
                path_2d, _ = section.to_planar()
                section_verts = path_2d.vertices
                radii = np.sqrt(section_verts[:, 0]**2 + section_verts[:, 1]**2)
            else:
                continue
        except Exception:
            # Fall back to vertex sampling
            mask = np.abs(axis_vals - pos) < sample_step
            if mask.sum() < 5:
                continue
            slice_verts = verts[mask]
            radii = np.sqrt(
                slice_verts[:, radial_axes[0]]**2 +
                slice_verts[:, radial_axes[1]]**2
            )

        if len(radii) < 5:
            continue

        # Separate inner (hole) and outer surfaces
        sorted_r = np.sort(radii)

        # Find gap between hole and outer surface
        gaps = np.diff(sorted_r)
        if len(gaps) == 0:
            continue

        # Look for significant gap (> 0.1mm) to separate hole from outer
        big_gap_idx = np.where(gaps > 0.1)[0]

        if len(big_gap_idx) > 0:
            # Use first big gap to separate inner from outer
            split_idx = big_gap_idx[0] + 1
            inner_radii = sorted_r[:split_idx]
            outer_radii = sorted_r[split_idx:]

            if len(inner_radii) > 0 and len(outer_radii) > 0:
                inner_r = inner_radii.max()
                outer_r = outer_radii.min()
            else:
                continue
        else:
            # No clear gap - use threshold
            threshold = hole_radius * 1.5
            inner_mask = radii < threshold
            outer_mask = radii >= threshold

            if inner_mask.sum() == 0 or outer_mask.sum() == 0:
                continue

            inner_r = radii[inner_mask].max()
            outer_r = radii[outer_mask].min()

        wall = outer_r - inner_r

        # Determine region based on outer radius
        if outer_r > hole_radius * 2.2:
            region = "worm"
        else:
            region = "shaft"

        result = WallThicknessResult(
            position=float(pos),
            inner_radius=float(inner_r),
            outer_radius=float(outer_r),
            wall_thickness=float(wall),
            region=region,
        )
        measurements.append(result)

        if wall < min_wall and wall > 0:
            min_wall = wall
            min_wall_pos = pos

    return WallAnalysis(
        min_wall=min_wall if min_wall != float('inf') else 0.0,
        min_wall_position=min_wall_pos,
        measurements=measurements,
    )


def analyze_peg_head_tap_hole(
    stl_path: Path,
    tap_drill_radius: float = 0.8,
    tap_depth: float = 4.0,
    repair: bool = True,
) -> tuple[MeshQuality, WallAnalysis]:
    """Analyze peg head STL for M2 tap hole wall thickness.

    The peg head has the shaft/worm axis along X (after rotation).
    The shaft end is at minimum X, peg head cap at maximum X.

    Args:
        stl_path: Path to peg head STL
        tap_drill_radius: Radius of tap drill hole (mm)
        tap_depth: Depth of tap hole (mm)
        repair: Whether to repair mesh before analysis

    Returns:
        Tuple of (MeshQuality, WallAnalysis)
    """
    if repair:
        mesh = load_and_repair_mesh(stl_path)
    else:
        import trimesh
        mesh = trimesh.load(stl_path)

    quality = check_mesh_quality(mesh)

    # Shaft end is at minimum X
    x_min = mesh.vertices[:, 0].min()

    # Analyze from shaft end into the worm
    raw_analysis = analyze_axial_wall_thickness(
        mesh,
        axis=0,  # X axis
        hole_radius=tap_drill_radius,
        sample_step=0.2,
        axis_range=(x_min, x_min + tap_depth + 1.0),
    )

    # Filter measurements: only keep those with hole radius close to expected
    # (within 20% of tap_drill_radius)
    tolerance = tap_drill_radius * 0.25
    valid_measurements = [
        m for m in raw_analysis.measurements
        if abs(m.inner_radius - tap_drill_radius) < tolerance
    ]

    # Recalculate minimum wall from valid measurements
    if valid_measurements:
        min_wall = min(m.wall_thickness for m in valid_measurements)
        min_wall_pos = next(
            m.position for m in valid_measurements
            if m.wall_thickness == min_wall
        )
    else:
        min_wall = 0.0
        min_wall_pos = 0.0

    return quality, WallAnalysis(
        min_wall=min_wall,
        min_wall_position=min_wall_pos,
        measurements=valid_measurements,
    )


def print_wall_analysis(
    quality: MeshQuality,
    analysis: WallAnalysis,
    title: str = "Wall Thickness Analysis",
) -> None:
    """Print wall thickness analysis results."""
    print(f"\n{title}")
    print("=" * 60)

    print(f"\nMesh Quality:")
    print(f"  Vertices: {quality.vertices:,}")
    print(f"  Faces: {quality.faces:,}")
    print(f"  Non-manifold edges: {quality.non_manifold_edges}")
    print(f"  Watertight: {quality.is_watertight}")
    if quality.is_watertight:
        print(f"  Volume: {quality.volume:.1f} mm³")

    print(f"\nWall Thickness Measurements:")
    print(f"{'Position':>10} | {'Hole r':>8} | {'Outer r':>8} | {'Wall':>8} | Region")
    print("-" * 55)

    for m in analysis.measurements:
        print(
            f"{m.position:>10.2f} | "
            f"{m.inner_radius:>8.3f} | "
            f"{m.outer_radius:>8.3f} | "
            f"{m.wall_thickness:>8.3f} | "
            f"{m.region}"
        )

    print()
    print(f"MINIMUM WALL: {analysis.min_wall:.3f}mm at position {analysis.min_wall_position:.2f}mm")


def calculate_theoretical_wall(
    tap_drill_radius: float = 0.8,
    tap_depth: float = 4.0,
    shaft_radius: float = 2.0,
    bearing_shaft_length: float = 1.3,
    worm_length: float = 7.6,
    worm_root_at_throat: float = 1.5,
    worm_root_at_end: float = 2.1,
) -> WallAnalysis:
    """Calculate theoretical wall thickness from known geometry.

    Uses the globoid worm profile to interpolate root radius at each depth.

    Args:
        tap_drill_radius: Radius of tap drill (mm)
        tap_depth: Depth of tap hole (mm)
        shaft_radius: Radius of bearing shaft (mm)
        bearing_shaft_length: Length of shaft beyond worm (mm)
        worm_length: Total worm length (mm)
        worm_root_at_throat: Worm root radius at throat/center (mm)
        worm_root_at_end: Worm root radius at worm ends (mm)

    Returns:
        WallAnalysis with theoretical measurements
    """
    measurements = []
    min_wall = float('inf')
    min_wall_depth = 0.0

    total_shaft = worm_length + bearing_shaft_length

    for depth in np.arange(0, tap_depth + 0.1, 0.25):
        pos_from_end = total_shaft - depth

        if pos_from_end > worm_length:
            # In bearing shaft region
            outer_r = shaft_radius
            region = "shaft"
        else:
            # In worm region - interpolate root radius
            # Worm center is at worm_length/2
            dist_from_center = abs(pos_from_end - worm_length / 2)
            # Linear interpolation from throat to end
            t = dist_from_center / (worm_length / 2)
            outer_r = worm_root_at_throat + t * (worm_root_at_end - worm_root_at_throat)
            region = "worm"

        wall = outer_r - tap_drill_radius

        if wall < min_wall:
            min_wall = wall
            min_wall_depth = depth

        measurements.append(WallThicknessResult(
            position=-depth,  # Negative = from shaft end
            inner_radius=tap_drill_radius,
            outer_radius=outer_r,
            wall_thickness=wall,
            region=region,
        ))

    return WallAnalysis(
        min_wall=min_wall,
        min_wall_position=-min_wall_depth,
        measurements=measurements,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m gib_tuners.utils.mesh_analysis <stl_path>")
        sys.exit(1)

    stl_path = Path(sys.argv[1])
    if not stl_path.exists():
        print(f"File not found: {stl_path}")
        sys.exit(1)

    quality, analysis = analyze_peg_head_tap_hole(stl_path)
    print_wall_analysis(quality, analysis, f"Mesh Analysis of {stl_path.name}")

    # Also show theoretical calculation
    # Use bh11-cd worm parameters (from mesh analysis earlier)
    print("\n" + "=" * 60)
    print("Theoretical Wall Thickness (bh11-cd worm geometry)")
    print("=" * 60)

    theoretical = calculate_theoretical_wall(
        tap_drill_radius=0.8,
        tap_depth=3.0,  # M2x3 screw
        shaft_radius=2.0,
        bearing_shaft_length=1.3,
        worm_length=7.6,
        worm_root_at_throat=1.5,  # From worm STEP analysis at Z=0
        worm_root_at_end=2.1,     # From worm STEP analysis at Z=3.8
    )
    print(f"\n{'Depth':>8} | {'Hole r':>8} | {'Root r':>8} | {'Wall':>8} | Region")
    print("-" * 55)
    for m in theoretical.measurements:
        print(
            f"{-m.position:>8.2f} | "
            f"{m.inner_radius:>8.3f} | "
            f"{m.outer_radius:>8.3f} | "
            f"{m.wall_thickness:>8.3f} | "
            f"{m.region}"
        )
    print()
    print(f"THEORETICAL MINIMUM WALL: {theoretical.min_wall:.3f}mm at {-theoretical.min_wall_position:.2f}mm depth")
