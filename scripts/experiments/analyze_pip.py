"""Analyze the pip geometry on the imported peg head STEP file."""

from pathlib import Path
from build123d import import_step, Part, Compound
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.GeomAbs import (
    GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone,
    GeomAbs_Sphere, GeomAbs_Torus, GeomAbs_BSplineSurface,
    GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse,
    GeomAbs_BezierCurve, GeomAbs_BSplineCurve,
)
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCP.BRep import BRep_Tool
from OCP.TopoDS import TopoDS
import math

REFERENCE_DIR = Path(__file__).parent.parent.parent / "reference"
PEG_HEAD_STEP = REFERENCE_DIR / "peghead7mm.step"

SURFACE_TYPE_NAMES = {
    GeomAbs_Plane: "Plane",
    GeomAbs_Cylinder: "Cylinder",
    GeomAbs_Cone: "Cone",
    GeomAbs_Sphere: "Sphere",
    GeomAbs_Torus: "Torus",
    GeomAbs_BSplineSurface: "BSpline",
}

def analyze_step():
    print(f"Loading: {PEG_HEAD_STEP}")
    imported = import_step(PEG_HEAD_STEP)

    if hasattr(imported, '__iter__') and not isinstance(imported, (Part, Compound)):
        shapes = list(imported)
        print(f"Imported {len(shapes)} shapes")
        if shapes:
            shape = shapes[0]
            for s in shapes[1:]:
                shape = shape + s
            shape = Part(shape.wrapped) if not isinstance(shape, Part) else shape
    else:
        shape = imported if isinstance(imported, Part) else Part(imported.wrapped)

    bb = shape.bounding_box()
    print(f"\nOverall bounding box:")
    print(f"  X: {bb.min.X:.3f} to {bb.max.X:.3f}  (width: {bb.max.X - bb.min.X:.3f})")
    print(f"  Y: {bb.min.Y:.3f} to {bb.max.Y:.3f}  (depth: {bb.max.Y - bb.min.Y:.3f})")
    print(f"  Z: {bb.min.Z:.3f} to {bb.max.Z:.3f}  (height: {bb.max.Z - bb.min.Z:.3f})")

    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, props)
    print(f"\nVolume: {props.Mass():.3f} mm³")

    # Analyze all faces
    print("\n--- Face Analysis ---")
    explorer = TopExp_Explorer(shape.wrapped, TopAbs_FACE)
    faces = []
    face_idx = 0
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        adaptor = BRepAdaptor_Surface(face)
        stype = adaptor.GetType()
        type_name = SURFACE_TYPE_NAMES.get(stype, f"Other({stype})")

        # Get face area
        face_props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face, face_props)
        area = face_props.Mass()

        info = {"idx": face_idx, "type": type_name, "area": area}

        if stype == GeomAbs_Cylinder:
            cyl = adaptor.Cylinder()
            radius = cyl.Radius()
            loc = cyl.Location()
            axis = cyl.Axis().Direction()
            info["radius"] = radius
            info["diameter"] = radius * 2
            info["center"] = (loc.X(), loc.Y(), loc.Z())
            info["axis"] = (axis.X(), axis.Y(), axis.Z())

        elif stype == GeomAbs_Plane:
            pln = adaptor.Plane()
            loc = pln.Location()
            normal = pln.Axis().Direction()
            info["location"] = (loc.X(), loc.Y(), loc.Z())
            info["normal"] = (normal.X(), normal.Y(), normal.Z())

        elif stype == GeomAbs_Cone:
            cone = adaptor.Cone()
            info["semi_angle_deg"] = math.degrees(cone.SemiAngle())
            loc = cone.Location()
            info["apex"] = (loc.X(), loc.Y(), loc.Z())

        elif stype == GeomAbs_Torus:
            torus = adaptor.Torus()
            info["major_radius"] = torus.MajorRadius()
            info["minor_radius"] = torus.MinorRadius()

        faces.append(info)
        face_idx += 1
        explorer.Next()

    print(f"Total faces: {len(faces)}")

    # Group by type
    by_type = {}
    for f in faces:
        by_type.setdefault(f["type"], []).append(f)

    print("\nFace type summary:")
    for t, fs in sorted(by_type.items()):
        print(f"  {t}: {len(fs)} faces")

    # Focus on small cylindrical faces (likely pip/stalk)
    print("\n--- Cylindrical Faces (sorted by radius) ---")
    cylinders = [f for f in faces if f["type"] == "Cylinder"]
    cylinders.sort(key=lambda f: f["radius"])

    for f in cylinders:
        cx, cy, cz = f["center"]
        ax, ay, az = f["axis"]
        print(f"  Face {f['idx']:3d}: r={f['radius']:.3f} (d={f['diameter']:.3f})  "
              f"area={f['area']:.3f}  center=({cx:.2f},{cy:.2f},{cz:.2f})  "
              f"axis=({ax:.2f},{ay:.2f},{az:.2f})")

    # Find pip candidates: small cylinders far from Z=0
    print("\n--- Pip Candidates (small cylinders with Z < -10) ---")
    pip_candidates = [f for f in cylinders
                      if f["diameter"] < 3.0 and f["center"][2] < -10]
    for f in pip_candidates:
        cx, cy, cz = f["center"]
        print(f"  Face {f['idx']:3d}: diameter={f['diameter']:.3f}  "
              f"area={f['area']:.3f}  center=({cx:.2f},{cy:.2f},{cz:.2f})")

    # Also look at small cones and tori (chamfers/fillets near pip)
    print("\n--- Cones (chamfers/transitions) ---")
    cones = [f for f in faces if f["type"] == "Cone"]
    for f in cones:
        print(f"  Face {f['idx']:3d}: semi_angle={f['semi_angle_deg']:.1f}°  "
              f"area={f['area']:.3f}  apex=({f['apex'][0]:.2f},{f['apex'][1]:.2f},{f['apex'][2]:.2f})")

    print("\n--- Tori (fillets/rounds) ---")
    tori = [f for f in faces if f["type"] == "Torus"]
    for f in tori:
        print(f"  Face {f['idx']:3d}: major_r={f['major_radius']:.3f}  "
              f"minor_r={f['minor_radius']:.3f}  area={f['area']:.3f}")

    # Find the most negative Z face (tip of pip)
    print("\n--- Extreme Z faces (most negative = pip tip) ---")
    # Check all face bounding boxes
    explorer2 = TopExp_Explorer(shape.wrapped, TopAbs_FACE)
    face_bbs = []
    idx = 0
    while explorer2.More():
        face = TopoDS.Face_s(explorer2.Current())
        adaptor = BRepAdaptor_Surface(face)
        # Sample face bounds
        u1, u2, v1, v2 = adaptor.FirstUParameter(), adaptor.LastUParameter(), \
                          adaptor.FirstVParameter(), adaptor.LastVParameter()

        face_props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face, face_props)
        com = face_props.CentreOfMass()

        face_bbs.append({
            "idx": idx,
            "com_z": com.Z(),
            "com_x": com.X(),
            "com_y": com.Y(),
        })
        idx += 1
        explorer2.Next()

    # Sort by center of mass Z
    face_bbs.sort(key=lambda f: f["com_z"])
    print("  5 most negative Z (center of mass):")
    for f in face_bbs[:5]:
        # Find matching face info
        match = next((fi for fi in faces if fi["idx"] == f["idx"]), None)
        type_str = match["type"] if match else "?"
        extra = ""
        if match and "diameter" in match:
            extra = f"  d={match['diameter']:.3f}"
        print(f"    Face {f['idx']:3d}: type={type_str}  "
              f"CoM=({f['com_x']:.2f},{f['com_y']:.2f},{f['com_z']:.2f}){extra}")


if __name__ == "__main__":
    analyze_step()
