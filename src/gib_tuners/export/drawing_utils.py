"""Shared helpers for the engineering-drawing scripts (scripts/*_drawing.py).

These supplement build123d_drafting with the project-specific pieces the peg
head drawing established: exact silhouette circles, plain text blocks, and a
shaded raster pictorial embedded into the exported SVG.
"""

import base64
from pathlib import Path

import numpy as np
from build123d import (
    Align, Compound, Edge, Face, GeomType, Location, Plane, Text, ThreePointArc,
    Wire,
)
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

    # Extent of the whole projection — a silhouette circle cannot exceed the
    # part's own projected footprint (guards the degenerate-fragment case)
    gb = Compound(children=list(edges)).bounding_box()

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
                    span = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]))
                    if span > 4 * tol:
                        # A real closed loop must span the circle it claims
                        if abs(span - 2 * R) > 4 * tol:
                            continue
                    else:
                        # Degenerate fragment (OCCT emits these where a tangent
                        # silhouette grazes the visible/hidden boundary): accept
                        # the circle only if it fits the projection's footprint —
                        # a sliver matching a distant axis would otherwise become
                        # a giant circle
                        if (c2[0] - R < gb.min.X - 2 or c2[0] + R > gb.max.X + 2 or
                                c2[1] - R < gb.min.Y - 2 or c2[1] + R > gb.max.Y + 2):
                            continue
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


def hatch_cut_faces(shape, axis_value, view_dir, proj_fn, spacing=1.5):
    """45-degree ISO 128-44 section hatching for planar cut faces.

    Finds the planar faces of `shape` whose normal is parallel to `view_dir`
    and which lie on the cutting plane (coordinate along view_dir equal to
    axis_value), then hatches them with 45-degree lines. Each hatch line is the
    intersection of the face with a plane, so holes and notches in the cut
    face clip the lines exactly.

    Args:
        shape: the sectioned solid (already scaled to drawing units)
        axis_value: cutting-plane coordinate along view_dir (scaled units)
        view_dir: world direction of the view axis, e.g. (0, 1, 0)
        proj_fn: (x, y, z) world point -> (page_x, page_y)
        spacing: hatch line spacing in page mm

    Returns a list of page-plane Edges.
    """
    vd = np.array(view_dir, dtype=float)
    vd /= np.linalg.norm(vd)
    cut_faces = []
    for f in shape.faces():
        if f.geom_type != GeomType.PLANE:
            continue
        n = f.normal_at(f.center())
        if abs(n.X * vd[0] + n.Y * vd[1] + n.Z * vd[2]) < 0.999:
            continue
        c = f.center()
        if abs(np.dot([c.X, c.Y, c.Z], vd) - axis_value) < 0.05:
            cut_faces.append(f)

    # Hatch planes: contain the view axis, normal at 45 degrees in the page
    # plane. For view_dir Y the plane x - z = d meets the cut face y = const
    # in the 45-degree line x - z = d.
    page_u = np.array((0, 0, 1.0)) if abs(vd[2]) < 0.9 else np.array((1.0, 0, 0))
    page_u -= vd * np.dot(page_u, vd)
    page_u /= np.linalg.norm(page_u)
    page_v = np.cross(vd, page_u)
    normal = (page_u - page_v) / np.sqrt(2)

    out = []
    for f in cut_faces:
        fb = f.bounding_box()
        corners = [(x, y, z) for x in (fb.min.X, fb.max.X)
                   for y in (fb.min.Y, fb.max.Y) for z in (fb.min.Z, fb.max.Z)]
        ds = [np.dot(c, normal) for c in corners]
        d = min(ds) + spacing * np.sqrt(2) / 2
        while d < max(ds):
            plane = Plane(origin=tuple(normal * d), z_dir=tuple(normal))
            for e in section_profile(f, plane=plane):
                p0, p1 = e.position_at(0), e.position_at(1)
                a, b = proj_fn(*p0), proj_fn(*p1)
                if np.linalg.norm(np.array(a) - b) > 1e-3:
                    out.append(Edge.make_line((*a, 0), (*b, 0)))
            d += spacing * np.sqrt(2)
    return out


def balloon(tip, centre, label, draft, radius=3.0):
    """ISO 6433 item-reference balloon: filled-arrow leader into a circled number.

    The leader runs from the arrowhead at `tip` toward the circle centre and
    stops at the circumference; the item number is centred in the circle.
    """
    t = np.array(tip[:2], dtype=float)
    c = np.array(centre[:2], dtype=float)
    u = (c - t) / np.linalg.norm(c - t)
    perp = np.array((-u[1], u[0]))
    head = [tuple(t) + (0,),
            tuple(t + u * 2.0 + perp * 0.5) + (0,),
            tuple(t + u * 2.0 - perp * 0.5) + (0,)]
    arrow = Face(Wire.make_polygon([*head, head[0]]))
    line = Edge.make_line((*t + u * 1.8, 0), (*c - u * radius, 0))
    circle = Edge.make_circle(radius, Plane((c[0], c[1], 0)))
    num = Location((c[0], c[1], 0)) * Text(
        label, font_size=draft.font_size, align=(Align.CENTER, Align.CENTER))
    return [arrow, line, circle, num]


def section_trace(p0, p1, arrow_dir, letter, letter_offset=None, font_size=3.5):
    """ISO 128-40 cutting-plane indication at the ends of a trace line.

    The trace itself (a chain line from p0 to p1) is drawn by the caller —
    typically an existing Centerline. This adds 3 mm thick end strokes
    extending beyond p0/p1, arrows in the viewing direction `arrow_dir`,
    and the identifying letter at each end.

    letter_offset: page-mm (dx, dy) of the letter from each arrowhead;
    default is 1.5 mm beyond the head along arrow_dir.

    Returns (thick_edges, marks): thick_edges belong on the part-weight
    layer, marks (arrow lines, filled heads, letters) on annotation layers.
    """
    a = np.array(p0[:2], dtype=float)
    b = np.array(p1[:2], dtype=float)
    u = (b - a) / np.linalg.norm(b - a)
    d = np.array(arrow_dir[:2], dtype=float)
    d /= np.linalg.norm(d)
    perp = np.array((-d[1], d[0]))
    thick, marks = [], []
    for end_pt, sgn in ((a, -1.0), (b, 1.0)):
        stroke_end = end_pt + sgn * u * 3
        thick.append(Edge.make_line((*end_pt, 0), (*stroke_end, 0)))
        arr_end = stroke_end + d * 5
        marks.append(Edge.make_line((*stroke_end, 0), (*arr_end, 0)))
        head = arr_end + d * 2
        marks.append(Face(Wire.make_polygon(
            [(*head, 0), (*arr_end + perp * 0.6, 0),
             (*arr_end - perp * 0.6, 0), (*head, 0)])))
        lbl = head + (np.array(letter_offset, dtype=float)
                      if letter_offset is not None else d * 1.5)
        marks.append(Location((lbl[0], lbl[1], 0)) * Text(
            letter, font_size=font_size, align=(Align.CENTER, Align.CENTER)))
    return thick, marks


def third_angle_symbol(x, y, h=5.0):
    """ISO 5456-2 third-angle projection symbol.

    Truncated-cone side view (trapezoid, small end toward the circles) with
    the small-end view (two concentric circles) placed on the small-end side
    — the third-angle arrangement. (x, y) is the circles' centre; h is the
    large diameter.
    """
    r, rs = h / 2, h / 4
    gap, length = 0.4 * h, h
    x0 = x + r + gap            # trapezoid small end
    x1 = x0 + length            # trapezoid large end
    out = [
        Edge.make_circle(r, Plane((x, y, 0))),
        Edge.make_circle(rs, Plane((x, y, 0))),
        Edge.make_line((x0, y - rs, 0), (x0, y + rs, 0)),
        Edge.make_line((x1, y - r, 0), (x1, y + r, 0)),
        Edge.make_line((x0, y - rs, 0), (x1, y - r, 0)),
        Edge.make_line((x0, y + rs, 0), (x1, y + r, 0)),
        Edge.make_line((x - r - 1.5, y, 0), (x1 + 1.5, y, 0)),  # centreline
    ]
    return out


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

    stl_path: a single path, or a list of paths / (path, rgb_color) tuples —
    use one STL per part for assemblies (export_stl of a multi-part Compound
    silently drops solids).
    """
    import gc

    import pyvista as pv

    if isinstance(stl_path, (str, Path)):
        stl_path = [stl_path]
    entries = [(e, BRASS) if isinstance(e, (str, Path)) else e for e in stl_path]

    plotter = pv.Plotter(off_screen=True, window_size=list(window_size))
    meshes = []
    for path, color in entries:
        mesh = pv.read(str(path))
        meshes.append(mesh)
        plotter.add_mesh(mesh, color=color, smooth_shading=True,
                         split_sharp_edges=True, feature_angle=35,
                         specular=0.5, specular_power=15)
    bounds = np.array([m.bounds for m in meshes])
    centre = [(bounds[:, 0].min() + bounds[:, 1].max()) / 2,
              (bounds[:, 2].min() + bounds[:, 3].max()) / 2,
              (bounds[:, 4].min() + bounds[:, 5].max()) / 2]
    cam = np.array(cam_dir, dtype=float)
    cam = cam / np.linalg.norm(cam) * dist
    plotter.camera_position = [tuple(np.array(centre) + cam), centre, (0, 0, 1)]
    plotter.camera.zoom(zoom)
    plotter.screenshot(png_path, transparent_background=True)
    plotter.close()
    del meshes, plotter
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
