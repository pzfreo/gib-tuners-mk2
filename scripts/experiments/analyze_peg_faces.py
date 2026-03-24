"""Dump all face types/dimensions for create_peg_head output (no worm).

Used to build the regression test: we snapshot every non-stalk face
and verify none of them change after the reinforcement fix.
"""

from build123d import Part
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.GeomAbs import (
    GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone,
    GeomAbs_Sphere, GeomAbs_Torus, GeomAbs_BSplineSurface,
)
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
from gib_tuners.components.peg_head import create_peg_head

SURFACE_TYPE_NAMES = {
    GeomAbs_Plane: "Plane",
    GeomAbs_Cylinder: "Cylinder",
    GeomAbs_Cone: "Cone",
    GeomAbs_Sphere: "Sphere",
    GeomAbs_Torus: "Torus",
    GeomAbs_BSplineSurface: "BSpline",
}


def dump_faces(shape, label=""):
    print(f"\n{'=' * 70}")
    print(f"  {label}")
    print(f"{'=' * 70}")

    bb = shape.bounding_box()
    print(f"Bounding box: X[{bb.min.X:.3f}, {bb.max.X:.3f}]  "
          f"Y[{bb.min.Y:.3f}, {bb.max.Y:.3f}]  Z[{bb.min.Z:.3f}, {bb.max.Z:.3f}]")
    print(f"Volume: {shape.volume:.4f} mm³")

    explorer = TopExp_Explorer(shape.wrapped, TopAbs_FACE)
    faces = []
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        adaptor = BRepAdaptor_Surface(face)
        stype = adaptor.GetType()
        type_name = SURFACE_TYPE_NAMES.get(stype, f"Other({stype})")

        props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face, props)
        area = props.Mass()
        com = props.CentreOfMass()

        info = {"type": type_name, "area": area,
                "com": (com.X(), com.Y(), com.Z())}

        if stype == GeomAbs_Cylinder:
            cyl = adaptor.Cylinder()
            info["diameter"] = cyl.Radius() * 2
            info["axis"] = tuple(
                round(v, 3) for v in (
                    cyl.Axis().Direction().X(),
                    cyl.Axis().Direction().Y(),
                    cyl.Axis().Direction().Z(),
                )
            )
        elif stype == GeomAbs_Torus:
            t = adaptor.Torus()
            info["major_r"] = t.MajorRadius()
            info["minor_r"] = t.MinorRadius()

        faces.append(info)
        explorer.Next()

    # Sort by type then area for stable comparison
    faces.sort(key=lambda f: (f["type"], -f["area"]))

    print(f"\nTotal faces: {len(faces)}")
    for i, f in enumerate(faces):
        extra = ""
        if "diameter" in f:
            extra = f"  d={f['diameter']:.3f}  axis={f['axis']}"
        if "major_r" in f:
            extra = f"  R={f['major_r']:.3f}  r={f['minor_r']:.3f}"
        cx, cy, cz = f["com"]
        print(f"  [{i:2d}] {f['type']:10s}  area={f['area']:8.3f}  "
              f"CoM=({cx:7.2f},{cy:7.2f},{cz:7.2f}){extra}")


config = create_default_config(scale=1.0, tolerance="production", hand=Hand.RIGHT)

# Without worm (simpler, what tests use)
peg_no_worm = create_peg_head(config, include_worm=False)
dump_faces(peg_no_worm, "create_peg_head(include_worm=False) — CURRENT (pre-fix)")
