#!/usr/bin/env python3
"""Validate production STEP files against a known-good baseline.

Checks that new build contains exactly the three expected changes vs sent/ptype/:
  1. Pip stalk reinforcement 1.0mm → 1.5mm  (peg_head)
  2. String hole 1.5mm → 1.7mm + chamfers   (string_post)
  3. Mounting holes 3.0mm → 3.2mm           (frame)

Usage:
    python scripts/check_production.py                          # sent/ptype/ vs output/
    python scripts/check_production.py --baseline sent/ptype/ --new sent/fixedv2/
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build123d import import_step, Part, Compound
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.BRepGProp import BRepGProp
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Torus, GeomAbs_Circle, GeomAbs_BSplineSurface
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
from OCP.GProp import GProp_GProps
from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS


PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"


def _load(path: Path) -> Part:
    imported = import_step(path)
    if hasattr(imported, "__iter__") and not isinstance(imported, (Part, Compound)):
        shapes = list(imported)
        shape = shapes[0]
        for s in shapes[1:]:
            shape = shape + s
        return Part(shape.wrapped) if not isinstance(shape, Part) else shape
    return imported if isinstance(imported, Part) else Part(imported.wrapped)


def _volume(shape: Part) -> float:
    """Volume via OCC — shape.volume returns 0 for STEP-imported shapes."""
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, props)
    return props.Mass()


def _cylinders(shape: Part) -> list[dict]:
    """Return all cylindrical faces with diameter, axis unit vector, area, and CoM."""
    results = []
    exp = TopExp_Explorer(shape.wrapped, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        adaptor = BRepAdaptor_Surface(face)
        if adaptor.GetType() == GeomAbs_Cylinder:
            cyl = adaptor.Cylinder()
            props = GProp_GProps()
            BRepGProp.SurfaceProperties_s(face, props)
            com = props.CentreOfMass()
            d = cyl.Axis().Direction()
            results.append({
                "diameter": cyl.Radius() * 2,
                "axis": (abs(d.X()), abs(d.Y()), abs(d.Z())),
                "area": props.Mass(),
                "com": (com.X(), com.Y(), com.Z()),
            })
        exp.Next()
    return results


def _has_chamfer_near_z(shape: Part, z: float, band: float = 1.5) -> bool:
    """Check for chamfer faces near a given Z.

    Chamfers at the intersection of two cylinders (string hole through post body)
    produce BSpline surfaces. Cone/Torus appear at simpler chamfer geometry.
    """
    exp = TopExp_Explorer(shape.wrapped, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        adaptor = BRepAdaptor_Surface(face)
        t = adaptor.GetType()
        if t in (GeomAbs_Cone, GeomAbs_Torus, GeomAbs_BSplineSurface):
            props = GProp_GProps()
            BRepGProp.SurfaceProperties_s(face, props)
            com = props.CentreOfMass()
            if abs(com.Z() - z) < band:
                return True
        exp.Next()
    return False


def _result(status, message):
    sym = {"PASS": "✓", "FAIL": "✗", "WARN": "!"}[status]
    return (status, f"  [{sym}] {message}")


def check_generic(name: str, baseline: Part, new: Part,
                  volume_delta_min: float, volume_delta_max: float) -> list:
    results = []
    vol_delta = _volume(new) - _volume(baseline)
    if volume_delta_min <= vol_delta <= volume_delta_max:
        results.append(_result(PASS, f"Volume delta {vol_delta:+.2f} mm³ (expected {volume_delta_min:+.0f} to {volume_delta_max:+.0f})"))
    elif abs(vol_delta) < 0.001:
        results.append(_result(WARN, f"Volume unchanged — expected delta for {name}"))
    else:
        results.append(_result(WARN, f"Volume delta {vol_delta:+.2f} mm³ outside expected range [{volume_delta_min:+.0f}, {volume_delta_max:+.0f}]"))

    bb_b = baseline.bounding_box()
    bb_n = new.bounding_box()
    bbox_ok = all(
        abs(getattr(bb_b.min, ax) - getattr(bb_n.min, ax)) < 0.05 and
        abs(getattr(bb_b.max, ax) - getattr(bb_n.max, ax)) < 0.05
        for ax in ("X", "Y", "Z")
    )
    if bbox_ok:
        results.append(_result(PASS, "Bounding box unchanged"))
    else:
        results.append(_result(FAIL,
            f"Bounding box changed: "
            f"X[{bb_b.min.X:.2f},{bb_b.max.X:.2f}]→[{bb_n.min.X:.2f},{bb_n.max.X:.2f}] "
            f"Y[{bb_b.min.Y:.2f},{bb_b.max.Y:.2f}]→[{bb_n.min.Y:.2f},{bb_n.max.Y:.2f}] "
            f"Z[{bb_b.min.Z:.2f},{bb_b.max.Z:.2f}]→[{bb_n.min.Z:.2f},{bb_n.max.Z:.2f}]"
        ))
    return results


def check_frame(baseline: Part, new: Part) -> list:
    results = check_generic("frame", baseline, new, volume_delta_min=-10, volume_delta_max=0)

    # Mounting holes: Z-axis cylinders, diameter 2.5–4.0mm, CoM near Z=-0.55 (through mounting plate)
    def mounting_holes(shape):
        return [c for c in _cylinders(shape)
                if c["axis"][2] > 0.9           # Z-axis
                and 2.5 < c["diameter"] < 4.0   # mounting hole size range
                and c["com"][2] > -2.0]          # near mounting plate

    baseline_mh = mounting_holes(baseline)
    new_mh = mounting_holes(new)

    if not new_mh:
        results.append(_result(FAIL, "No mounting holes detected in new frame"))
    else:
        diameters = sorted(set(round(c["diameter"], 2) for c in new_mh))
        if all(abs(d - 3.2) < 0.1 for d in diameters):
            results.append(_result(PASS, f"Mounting holes ≈ 3.2mm (found {diameters})"))
        else:
            results.append(_result(FAIL, f"Mounting holes unexpected diameters: {diameters} (expected ~3.2mm)"))

    if baseline_mh:
        base_diams = sorted(set(round(c["diameter"], 2) for c in baseline_mh))
        if all(abs(d - 3.0) < 0.1 for d in base_diams):
            results.append(_result(PASS, f"Baseline mounting holes confirmed ≈ 3.0mm"))
        else:
            results.append(_result(WARN, f"Baseline mounting holes: {base_diams} (expected ~3.0mm)"))

    return results


def check_string_post(baseline: Part, new: Part) -> list:
    results = check_generic("string_post", baseline, new, volume_delta_min=-5, volume_delta_max=0)

    # String hole: Y-axis cylinder with small diameter
    def string_holes(shape):
        return [c for c in _cylinders(shape)
                if c["axis"][1] > 0.9          # Y-axis (cross-drilled)
                and c["diameter"] < 3.0]        # small hole

    new_holes = string_holes(new)
    baseline_holes = string_holes(baseline)

    if not new_holes:
        results.append(_result(FAIL, "No Y-axis string hole found in new string_post"))
    else:
        diameters = sorted(set(round(c["diameter"], 2) for c in new_holes))
        if any(abs(d - 1.7) < 0.1 for d in diameters):
            results.append(_result(PASS, f"String hole ≈ 1.7mm (found {diameters})"))
        else:
            results.append(_result(FAIL, f"String hole unexpected: {diameters} (expected ~1.7mm)"))

    if baseline_holes:
        base_diams = sorted(set(round(c["diameter"], 2) for c in baseline_holes))
        if any(abs(d - 1.5) < 0.1 for d in base_diams):
            results.append(_result(PASS, "Baseline string hole confirmed ≈ 1.5mm"))
        else:
            results.append(_result(WARN, f"Baseline string hole: {base_diams} (expected ~1.5mm)"))

    # Chamfers: cone or torus faces near the string hole Z position
    if new_holes:
        hole_z = new_holes[0]["com"][2]
        if _has_chamfer_near_z(new, hole_z):
            results.append(_result(PASS, "Chamfer faces present at string hole"))
        else:
            results.append(_result(FAIL, "No chamfer faces found at string hole"))

        if not _has_chamfer_near_z(baseline, hole_z):
            results.append(_result(PASS, "Baseline confirmed: no chamfer at string hole"))

    return results


def check_peg_head(baseline: Part, new: Part) -> list:
    results = check_generic("peg_head", baseline, new, volume_delta_min=0, volume_delta_max=5)

    def _pip_stalk_diameter(shape) -> float | None:
        """Find pip stalk diameter: the thinnest X-axis cylinder at the pip end.

        Works for both RH (pip at +X) and LH (pip at -X after mirroring).
        Uses the most extreme |comX| to find the pip region, ignoring the
        tap hole which is small but at the opposite end.
        """
        candidates = [c for c in _cylinders(shape)
                      if c["axis"][0] > 0.9 and c["diameter"] < 2.5]
        if not candidates:
            return None
        # Find the cylinder with the most extreme X position (pip end)
        pip_end = max(candidates, key=lambda c: abs(c["com"][0]))
        # Now find all cylinders near that extreme X and return minimum diameter
        pip_x = abs(pip_end["com"][0])
        pip_region = [c for c in candidates if abs(abs(c["com"][0]) - pip_x) < 3.0]
        return min(c["diameter"] for c in pip_region)

    new_d = _pip_stalk_diameter(new)
    base_d = _pip_stalk_diameter(baseline)

    if new_d is None:
        results.append(_result(WARN, "No pip stalk cylinders detected — face may be consumed by boolean"))
    elif new_d >= 1.4:
        results.append(_result(PASS, f"Pip stalk {new_d:.2f}mm ≥ 1.4mm (reinforced)"))
    else:
        results.append(_result(FAIL, f"Pip stalk still thin: {new_d:.2f}mm (expected ≥ 1.4mm)"))

    if base_d is not None:
        if base_d < 1.2:
            results.append(_result(PASS, f"Baseline pip stalk confirmed thin: {base_d:.2f}mm"))
        else:
            results.append(_result(WARN, f"Baseline pip stalk: {base_d:.2f}mm (expected ~1.0mm)"))

    return results


COMPONENTS = {
    "frame_rh_5gang": check_frame,
    "frame_lh_5gang": check_frame,
    "string_post":    check_string_post,
    "peg_head_rh":    check_peg_head,
    "peg_head_lh":    check_peg_head,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate production STEP files vs baseline")
    parser.add_argument("--baseline", type=Path, default=Path("sent/ptype"),
                        help="Baseline directory (default: sent/ptype/)")
    parser.add_argument("--new", type=Path, default=Path("output"),
                        help="New build directory (default: output/)")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero on warnings or skipped components "
                             "(for release gating, where WARN must not ship)")
    args = parser.parse_args()

    all_pass = True
    any_fail = False
    any_skip = False

    # Sanity check: LH and RH frames in new build must be same file size
    lh = args.new / "frame_lh_5gang.step"
    rh = args.new / "frame_rh_5gang.step"
    if lh.exists() and rh.exists():
        lh_size, rh_size = lh.stat().st_size, rh.stat().st_size
        if lh_size == rh_size:
            print(f"  [✓] LH/RH frames identical size ({lh_size:,} bytes) — labels off confirmed")
        else:
            print(f"  [!] LH/RH frame sizes differ: LH={lh_size:,} RH={rh_size:,} — check --label-frames")
            all_pass = False

    for name, checker in COMPONENTS.items():
        baseline_path = args.baseline / f"{name}.step"
        new_path = args.new / f"{name}.step"

        if not baseline_path.exists():
            print(f"\n{name}: SKIP (baseline not found: {baseline_path})")
            any_skip = True
            continue
        if not new_path.exists():
            print(f"\n{name}: SKIP (new file not found: {new_path})")
            any_skip = True
            continue

        print(f"\n{name}")
        print(f"  Loading baseline ({baseline_path.stat().st_size // 1024} KB)...", end=" ", flush=True)
        baseline = _load(baseline_path)
        print(f"vol={_volume(baseline):.1f} mm³")
        print(f"  Loading new      ({new_path.stat().st_size // 1024} KB)...", end=" ", flush=True)
        new = _load(new_path)
        print(f"vol={_volume(new):.1f} mm³")

        results = checker(baseline, new)
        for status, msg in results:
            print(msg)
            if status == FAIL:
                any_fail = True
                all_pass = False
            elif status == WARN:
                all_pass = False

    print()
    if any_fail:
        print("RESULT: FAIL — one or more checks failed")
        return 1
    elif not all_pass:
        print("RESULT: WARN — passed with warnings, review above")
        # A warning is advisory interactively, but the LH/RH size mismatch that
        # catches a labelled-frame build lands here — it must block a release.
        return 1 if args.strict else 0
    elif any_skip:
        print("RESULT: SKIP — some components were not checked, review above")
        # Nothing was validated for those components; only a build that emitted
        # no files gets here, which must not read as a pass when gating.
        return 1 if args.strict else 0
    else:
        print("RESULT: PASS — all checks passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
