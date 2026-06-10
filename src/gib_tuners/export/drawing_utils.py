"""Shared helpers for the engineering-drawing scripts (scripts/*_drawing.py).

These supplement build123d_drafting with the project-specific pieces the peg
head drawing established: exact silhouette circles, plain text blocks, and a
shaded raster pictorial embedded into the exported SVG.
"""

import base64

import numpy as np
from build123d import Align, Edge, GeomType, Location, Plane, Text, ThreePointArc
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_SurfaceType as ST

BRASS = (0.80, 0.64, 0.32)


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
                return ThreePointArc(snap(pts[0]), snap(pts[len(pts) // 2]), snap(pts[-1]))
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
