"""Shared helpers for the engineering-drawing scripts (scripts/*_drawing.py).

These supplement build123d_drafting with the project-specific pieces the peg
head drawing established: exact silhouette circles, plain text blocks, and a
shaded raster pictorial embedded into the exported SVG.
"""

import base64

import numpy as np
from build123d import Align, Edge, Face, GeomType, Location, Plane, Text, ThreePointArc
from build123d.geometry import TOLERANCE
from build123d.topology import downcast
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.BRepLib import BRepLib
from OCP.GeomAbs import GeomAbs_SurfaceType as ST
from OCP.gp import gp_Ax1, gp_Ax2, gp_Dir, gp_Pnt
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.TopAbs import TopAbs_ShapeEnum
from OCP.TopExp import TopExp_Explorer

BRASS = (0.80, 0.64, 0.32)


def project_visible(shape, viewport_origin, viewport_up, look_at, include_smooth=True):
    """Visible-edge HLR projection with optional smooth-edge suppression.

    Same projection as build123d's project_to_viewport, but the Rg1 class
    (tangent-continuous "regular" edges) can be dropped. Lofted/patched
    geometry — e.g. gear teeth from the external gear calculator — carries
    tangent seam edges between surface patches; HLR draws every one, striping
    each flank. Sharp edges and silhouettes are unaffected.

    Returns a list of visible Edges in raw viewport coordinates.
    """
    algo = HLRBRep_Algo()
    algo.Add(shape.wrapped)
    direction = (np.array(viewport_origin, dtype=float) - np.array(look_at, dtype=float))
    direction /= np.linalg.norm(direction)
    ax = gp_Ax2()
    ax.SetAxis(gp_Ax1(gp_Pnt(*viewport_origin), gp_Dir(*direction)))
    ax.SetYDirection(gp_Dir(*viewport_up))
    algo.Projector(HLRAlgo_Projector(ax))
    algo.Update()
    algo.Hide()
    hlr = HLRBRep_HLRToShape(algo)
    compounds = [hlr.VCompound(), hlr.OutLineVCompound()]
    if include_smooth:
        compounds.append(hlr.Rg1LineVCompound())
    edges = []
    for comp in compounds:
        if comp.IsNull():
            continue
        BRepLib.BuildCurves3d_s(comp, TOLERANCE)
        ex = TopExp_Explorer(comp, TopAbs_ShapeEnum.TopAbs_EDGE)
        while ex.More():
            edges.append(Edge(downcast(ex.Current())))
            ex.Next()
    return edges


def section_profile(shape, plane=Plane.XY, size=1000):
    """Edges of the shape's cross-section on the given plane.

    Uses BRepAlgoAPI_Section, so it works on shells (e.g. imported gear STEPs)
    as well as solids. The returned edges lie in world coordinates on the
    section plane — for an XY section they are already page-plane (x, y, 0)
    curves. A transverse mid-face section is the conventional way to show a
    helical gear's tooth profile: a direct axial HLR view shows both end
    profiles twisted by the helix advance.
    """
    plane_face = Face.make_rect(size, size, plane)
    sec = BRepAlgoAPI_Section(shape.wrapped, plane_face.wrapped)
    sec.Build()
    edges = []
    ex = TopExp_Explorer(sec.Shape(), TopAbs_ShapeEnum.TopAbs_EDGE)
    while ex.More():
        edges.append(Edge(downcast(ex.Current())))
        ex.Next()
    return edges


def exactify_silhouettes(edges, faces, view_dir, proj_fn, tol=0.12):
    """Replace faceted silhouette polylines with exact circular arcs.

    OCCT's exact HLR emits silhouette ("outline") curves on doubly-curved faces
    as degree-1 BSplines (~15-point polylines). Any surface of revolution viewed
    along its axis has circular silhouettes, so for each revolved face whose
    axis is parallel to the view direction we know the silhouette circle's
    CENTRE exactly (the projected axis). A polyline is replaced only when every
    vertex is equidistant from such a known centre within tol (in projected,
    i.e. scaled, mm) — the radius comes from the vertices, the centre is never
    fitted. Inapplicable cases are left untouched.

    Args:
        edges: projected edges from project_to_viewport (raw view coords)
        faces: faces of the projected (scaled) solid
        view_dir: world direction of the view axis, e.g. (0, 1, 0)
        proj_fn: gp_Pnt -> (page_x, page_y) in the same raw view coords

    Returns:
        (new_edges, replaced_count)
    """
    centres = []
    for f in faces:
        surf = BRepAdaptor_Surface(f.wrapped)
        st = surf.GetType()
        if st == ST.GeomAbs_Torus:
            ax = surf.Torus().Position().Axis()
        elif st == ST.GeomAbs_Sphere:
            centres.append(np.array(proj_fn(surf.Sphere().Location())))
            continue
        elif st == ST.GeomAbs_SurfaceOfRevolution:
            ax = surf.AxeOfRevolution()
        elif st in (ST.GeomAbs_Cylinder, ST.GeomAbs_Cone):
            ax = (surf.Cylinder() if st == ST.GeomAbs_Cylinder else surf.Cone()).Axis()
        else:
            continue
        d = ax.Direction()
        if abs(d.X() * view_dir[0] + d.Y() * view_dir[1] + d.Z() * view_dir[2]) > 0.999:
            centres.append(np.array(proj_fn(ax.Location())))

    def replacement(e):
        if e.geom_type != GeomType.BSPLINE:
            return None
        sp = e.geom_adaptor().Curve().Curve()
        if sp.Degree() != 1:
            return None
        if sp.NbPoles() < 4:
            return None  # too short to be a faceted silhouette; arc would degenerate
        tr = e.location.wrapped.Transformation()
        pts = np.array([[p.X(), p.Y(), p.Z()] for p in
                        (sp.Pole(i + 1).Transformed(tr) for i in range(sp.NbPoles()))])
        for c2 in centres:
            dist = np.linalg.norm(pts[:, :2] - c2, axis=1)
            if dist.max() - dist.min() < tol:
                R = dist.mean()
                z = pts[0, 2]

                def snap(p):
                    v = p[:2] - c2
                    v = v / np.linalg.norm(v) * R
                    return (c2[0] + v[0], c2[1] + v[1], z)

                if np.linalg.norm(pts[0, :2] - pts[-1, :2]) < tol:
                    return Edge.make_circle(R, Plane((c2[0], c2[1], z)))
                try:
                    return ThreePointArc(snap(pts[0]), snap(pts[len(pts) // 2]), snap(pts[-1]))
                except Exception:
                    return None  # degenerate (collinear/coincident) — keep the polyline
        return None

    out, n = [], 0
    for e in edges:
        rep = replacement(e)
        out.append(rep if rep is not None else e)
        n += rep is not None
    return out, n


def text_block(lines, x, y, line_h=4.5, size=2.5):
    """Left-justified block of text lines starting at page (x, y), going down."""
    out = []
    for i, line in enumerate(lines):
        t = Text(line, font_size=size, align=(Align.MIN, Align.MAX))
        out.append(Location((x, y - i * line_h, 0)) * t)
    return out


def render_shaded_pictorial(stl_path, png_path, cam_dir, dist, window_size, zoom=1.5):
    """Shaded raster pictorial via pyvista.

    HLR line projections of threads and grooves read poorly (the visible
    boundary decomposes into ring-like curves), so pictorials are rendered
    shaded. split_sharp_edges keeps crisp feature edges under smooth shading.
    """
    import gc

    import pyvista as pv

    mesh = pv.read(stl_path)
    plotter = pv.Plotter(off_screen=True, window_size=list(window_size))
    plotter.add_mesh(mesh, color=BRASS, smooth_shading=True,
                     split_sharp_edges=True, feature_angle=35,
                     specular=0.5, specular_power=15)
    cam = np.array(cam_dir, dtype=float)
    cam = cam / np.linalg.norm(cam) * dist
    plotter.camera_position = [tuple(np.array(mesh.center) + cam), mesh.center, (0, 0, 1)]
    plotter.camera.zoom(zoom)
    plotter.screenshot(png_path, transparent_background=True)
    plotter.close()
    del mesh, plotter
    gc.collect()  # tear down VTK objects before interpreter shutdown noise


def embed_png_in_svg(svg_path, png_path, x, y_bottom, w, h):
    """Insert a raster image into a build123d ExportSVG file at page coords.

    The image element goes outside the scale(1,-1) group, so svg_y = -page_y
    with the image anchored at its top edge.
    """
    with open(png_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    image_el = (f'<image x="{x}" y="{-(y_bottom + h)}" width="{w}" height="{h}" '
                f'preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{b64}"/>')
    svg_text = svg_path.read_text()
    svg_path.write_text(svg_text.replace('</svg>', image_el + '\n</svg>'))
