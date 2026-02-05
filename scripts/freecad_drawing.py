#!/usr/bin/env python3
"""Generate engineering drawings from STEP files using FreeCAD TechDraw.

This script runs under FreeCAD's Python interpreter (via the FreeCAD GUI binary).
It imports a STEP file, creates a TechDraw page with orthographic views,
dimensions, and exports to PDF/SVG.

Usage (called by scripts/drawings.py, not directly):
    /Applications/FreeCAD.app/Contents/MacOS/FreeCAD scripts/freecad_drawing.py

Arguments are passed via environment variables:
    DRAWING_STEP_FILE  - Path to input STEP file
    DRAWING_OUTPUT_DIR - Output directory for PDF/SVG/FCStd
    DRAWING_COMPONENT  - Component name (frame, string_post, wheel, peg_head)
    DRAWING_TITLE      - Drawing title
    DRAWING_HAND       - Hand variant (rh/lh)
    DRAWING_GEAR       - Gear config name (for title block)
"""

import math
import os
import sys
import time

import FreeCAD as App
import FreeCADGui as Gui
import Part

# Process Qt events to let projections compute
from PySide2 import QtCore

# ANSI A landscape page: 279.4 x 215.9 mm
# Drawable area inside border: ~13mm to ~267mm horizontal, ~13mm to ~203mm vertical
# Title block: bottom-right, ~120mm wide x ~50mm tall
# Usable area above title block: ~13mm to ~267mm x ~13mm to ~163mm
PAGE_W = 279.4
PAGE_H = 215.9
MARGIN = 15
TITLE_BLOCK_H = 52  # approximate height of title block area


# --- Utility functions ---

def process_events(seconds=10):
    """Process Qt events for given duration to allow projection threads."""
    for _ in range(int(seconds * 10)):
        QtCore.QCoreApplication.processEvents()
        time.sleep(0.1)


def find_view_items(doc):
    """Find all DrawProjGroupItem views in the document."""
    items = {}
    for obj in doc.Objects:
        if obj.TypeId == "TechDraw::DrawProjGroupItem":
            items[obj.Type] = obj
    return items


def get_vertices(view, max_count=500):
    """Get all vertex positions from a view.

    Returns list of (index, x, y) tuples.
    Note: TechDraw vertex Y is negated relative to edge geometry Y.
    """
    vertices = []
    for i in range(max_count):
        try:
            v = view.getVertexByIndex(i)
            if v is None:
                break
            vx = getattr(v, "x", getattr(v, "X", None))
            vy = getattr(v, "y", getattr(v, "Y", None))
            if vx is not None and vy is not None:
                vertices.append((i, vx, vy))
        except Exception:
            break
    return vertices


def get_circles(view):
    """Find all circular edges in a view.

    Returns list of (edge_index, center_x, center_y, radius) tuples.
    """
    circles = []
    try:
        edges = view.getVisibleEdges()
        for i, edge in enumerate(edges):
            try:
                curve = edge.Curve
                if hasattr(curve, "Radius") and hasattr(curve, "Center"):
                    span = abs(edge.LastParameter - edge.FirstParameter)
                    if span > 5.0:  # nearly full circle
                        c = curve.Center
                        circles.append((i, c.x, c.y, curve.Radius))
            except Exception:
                pass
    except Exception:
        pass
    return circles


def find_vertex_near(vertices, x, y, tol=1.0):
    """Find vertex index nearest to (x, y) within tolerance."""
    best_idx = None
    best_dist = float("inf")
    for idx, vx, vy in vertices:
        d = math.sqrt((vx - x) ** 2 + (vy - y) ** 2)
        if d < best_dist and d < tol:
            best_dist = d
            best_idx = idx
    return best_idx


def find_unique_radii(circles, tol=0.05):
    """Group circles by radius, return {radius: [(edge_idx, cx, cy)]}."""
    groups = {}
    for edge_idx, cx, cy, r in circles:
        r_key = round(r / tol) * tol
        if r_key not in groups:
            groups[r_key] = []
        groups[r_key].append((edge_idx, cx, cy))
    return groups


# --- Dimension helper ---

_dim_counter = [0]


def add_dim(doc, page, view, dim_type, refs, x_off=0, y_off=0,
            fmt="", name_prefix="Dim", fontsize=3.5):
    """Add a TechDraw dimension with proper font settings."""
    actual_name = f"{name_prefix}{_dim_counter[0]}"
    _dim_counter[0] += 1

    dim = doc.addObject("TechDraw::DrawViewDimension", actual_name)
    dim.Type = dim_type
    dim.References2D = [(view, refs)]
    if fmt:
        dim.FormatSpec = fmt
    dim.X = x_off
    dim.Y = y_off
    page.addView(dim)

    vo = dim.ViewObject
    if vo:
        vo.Font = "Helvetica"
        vo.Fontsize = fontsize
        vo.Arrowsize = 2.5

    return dim


# --- Page creation ---

def create_page(doc, template_name="ANSIA_Landscape.svg"):
    """Create a TechDraw page with template."""
    resource_dir = App.getResourceDir()
    template_path = resource_dir + "Mod/TechDraw/Templates/" + template_name

    page = doc.addObject("TechDraw::DrawPage", "Page")
    tpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
    tpl.Template = template_path
    page.Template = tpl
    page.KeepUpdated = True
    doc.recompute()

    return page, tpl


def fill_title_block(tpl, title, gear="", scale_text="1:1"):
    """Fill template title block fields."""
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")

    fields = {
        "CompanyName": "gib-tuners",
        "DrawingTitle1": title,
        "DrawingTitle2": gear,
        "Scale": scale_text,
    }
    for key, val in fields.items():
        try:
            tpl.setEditFieldContent(key, val)
        except Exception:
            pass


# ============================================================
# FRAME
# ============================================================

def create_frame_drawing(doc, page, obj):
    """Create frame drawing: side elevation + top view + end view + isometric.

    Layout on ANSI A landscape (279.4 x 215.9):
        Row 1: Top/plan view (above anchor)
        Row 2: Side elevation (anchor) + End view (right)
        Lower-left: Isometric view
    No bottom view - it's redundant with top view for this geometry.
    """
    group = doc.addObject("TechDraw::DrawProjGroup", "ProjGroup")
    page.addView(group)

    group.Source = [obj]
    group.ProjectionType = "Third Angle"
    group.ScaleType = "Custom"
    group.Scale = 1.0

    # Front anchor = side elevation (looking from -X direction)
    group.addProjection("Front")
    group.Anchor.Direction = App.Vector(-1, 0, 0)
    group.Anchor.XDirection = App.Vector(0, 1, 0)

    # Top = plan view (looking down from +Z)
    group.addProjection("Top")
    # Right = end view (looking from +Y end)
    group.addProjection("Right")

    # Position: centered horizontally, upper half of page
    # Frame is 145mm wide at 1:1 - needs ~160mm with dimension clearance
    # Place group so side view sits in the upper-middle area
    group.X = 115
    group.Y = 100

    doc.recompute()
    process_events(8)
    doc.recompute()

    # Isometric view - lower left, clear of views and title block
    iso = doc.addObject("TechDraw::DrawViewPart", "IsoView")
    iso.Source = [obj]
    iso.Direction = App.Vector(1, -1, -1)
    iso.XDirection = App.Vector(0, 1, -1)
    iso.ScaleType = "Custom"
    iso.Scale = 0.7
    iso.X = 65
    iso.Y = 50
    page.addView(iso)

    doc.recompute()
    process_events(5)
    doc.recompute()

    return group, iso


def add_frame_dimensions(doc, page):
    """Add dimensions to frame drawing views."""
    items = find_view_items(doc)
    front = items.get("Front")
    top = items.get("Top")
    right = items.get("Right")

    if not front:
        return

    front_verts = get_vertices(front)
    front_circles = get_circles(front)

    if not front_verts:
        return

    xs = [v[1] for v in front_verts]
    ys = [v[2] for v in front_verts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    # === FRONT (Side elevation) ===

    # Overall length: top edge corners (ymin in vertex coords = top in view)
    v_left = find_vertex_near(front_verts, xmin, ymin)
    v_right = find_vertex_near(front_verts, xmax, ymin)
    if v_left is not None and v_right is not None:
        add_dim(doc, page, front, "DistanceX",
                (f"Vertex{v_left}", f"Vertex{v_right}"),
                y_off=12, name_prefix="DimLen")

    # Find the inner gap Y level (not min/max)
    gap_y_verts = sorted(set(round(v[2], 1) for v in front_verts))
    inner_ys = [y for y in gap_y_verts
                if abs(y - ymin) > 0.5 and abs(y - ymax) > 0.5]

    if inner_ys:
        gap_y = inner_ys[0]
        gap_verts = [(idx, vx) for idx, vx, vy in front_verts
                     if abs(vy - gap_y) < 0.2]
        gap_verts.sort(key=lambda v: v[1])

        # End length: leftmost gap vertices
        if len(gap_verts) >= 2:
            add_dim(doc, page, front, "DistanceX",
                    (f"Vertex{gap_verts[0][0]}", f"Vertex{gap_verts[1][0]}"),
                    y_off=-10, name_prefix="DimEnd")

        # Housing length: at bottom edge (ymax in vertex coords)
        bottom_verts = [(idx, vx) for idx, vx, vy in front_verts
                        if abs(vy - ymax) < 0.2]
        bottom_verts.sort(key=lambda v: v[1])

        if len(bottom_verts) >= 2:
            add_dim(doc, page, front, "DistanceX",
                    (f"Vertex{bottom_verts[0][0]}",
                     f"Vertex{bottom_verts[1][0]}"),
                    y_off=-17, name_prefix="DimHsg")

        # Pitch: first housing start to second housing start
        if len(bottom_verts) >= 4:
            add_dim(doc, page, front, "DistanceX",
                    (f"Vertex{bottom_verts[0][0]}",
                     f"Vertex{bottom_verts[2][0]}"),
                    y_off=-24, name_prefix="DimPitch")

    # Wall thickness: two vertices at leftmost X
    left_verts = [(idx, vy) for idx, vx, vy in front_verts
                  if abs(vx - xmin) < 0.2]
    left_verts.sort(key=lambda v: v[1])
    if len(left_verts) >= 2:
        add_dim(doc, page, front, "DistanceY",
                (f"Vertex{left_verts[0][0]}",
                 f"Vertex{left_verts[1][0]}"),
                x_off=-15, name_prefix="DimWall")

    # Side hole diameter - pick the rightmost circle (away from crowded left)
    if front_circles:
        radii = find_unique_radii(front_circles)
        for r, circles_list in sorted(radii.items()):
            # Pick rightmost circle
            rightmost = max(circles_list, key=lambda c: c[1])
            add_dim(doc, page, front, "Diameter",
                    (f"Edge{rightmost[0]}",),
                    x_off=5, y_off=-10, name_prefix="DimSideHole")
            break

    # === TOP (Plan) view - hole diameters ===
    if top:
        top_circles = get_circles(top)
        if top_circles:
            radii = find_unique_radii(top_circles)
            sig_radii = {r: cs for r, cs in radii.items() if r >= 1.0}
            sorted_radii = sorted(sig_radii.items())

            # Spread labels: pick circles at distinct X positions,
            # alternate leader direction
            for i, (r, circles_list) in enumerate(sorted_radii):
                # Sort circles by X position
                by_x = sorted(circles_list, key=lambda c: c[1])
                n = len(by_x)

                if i == 0:
                    # Smallest holes: pick rightmost, leader goes right-up
                    pick = by_x[-1]
                    x_off, y_off = 18, 8
                elif i == len(sorted_radii) - 1:
                    # Largest holes: pick leftmost, leader goes left-up
                    pick = by_x[0]
                    x_off, y_off = -22, 8
                else:
                    # Middle: pick center, leader goes right-down
                    pick = by_x[n // 2]
                    x_off, y_off = 18, -8

                add_dim(doc, page, top, "Diameter",
                        (f"Edge{pick[0]}",),
                        x_off=x_off, y_off=y_off,
                        name_prefix="DimTopHole")

    # === RIGHT (End cross-section) ===
    if right:
        right_verts = get_vertices(right)
        if right_verts:
            rxs = [v[1] for v in right_verts]
            rys = [v[2] for v in right_verts]

            # Outer width
            v_bl = find_vertex_near(right_verts, min(rxs), min(rys))
            v_br = find_vertex_near(right_verts, max(rxs), min(rys))
            if v_bl is not None and v_br is not None:
                add_dim(doc, page, right, "DistanceX",
                        (f"Vertex{v_bl}", f"Vertex{v_br}"),
                        y_off=8, name_prefix="DimEndW")

            # Outer height
            v_tl = find_vertex_near(right_verts, min(rxs), max(rys))
            if v_bl is not None and v_tl is not None:
                add_dim(doc, page, right, "DistanceY",
                        (f"Vertex{v_bl}", f"Vertex{v_tl}"),
                        x_off=-8, name_prefix="DimEndH")


# ============================================================
# STRING POST
# ============================================================

def create_string_post_drawing(doc, page, obj):
    """Create string post drawing: side profile + end view."""
    group = doc.addObject("TechDraw::DrawProjGroup", "ProjGroup")
    page.addView(group)

    group.Source = [obj]
    group.ProjectionType = "Third Angle"
    group.ScaleType = "Custom"
    group.Scale = 5.0  # 5:1

    # Front = side profile
    group.addProjection("Front")
    group.Anchor.Direction = App.Vector(0, -1, 0)
    group.Anchor.XDirection = App.Vector(1, 0, 0)

    # Right = end view (circular cross-section)
    group.addProjection("Right")

    # Position: left-center of page
    group.X = 85
    group.Y = 90

    doc.recompute()
    process_events(8)
    doc.recompute()

    return group, None


def add_string_post_dimensions(doc, page):
    """Add dimensions to string post drawing."""
    items = find_view_items(doc)
    front = items.get("Front")
    right = items.get("Right")

    if front:
        front_verts = get_vertices(front)
        if front_verts:
            ys = [v[2] for v in front_verts]
            xs = [v[1] for v in front_verts]

            # Overall height
            v_bot = find_vertex_near(front_verts, 0, min(ys),
                                     tol=abs(max(xs)) + 1)
            v_top = find_vertex_near(front_verts, 0, max(ys),
                                     tol=abs(max(xs)) + 1)
            if v_bot is not None and v_top is not None and v_bot != v_top:
                add_dim(doc, page, front, "DistanceY",
                        (f"Vertex{v_bot}", f"Vertex{v_top}"),
                        x_off=-20, name_prefix="DimPostH")

            # Width dimensions at distinct Y levels (cap, bearing, shaft)
            # Group vertices by Y to find the stepped profile widths
            y_groups = {}
            for idx, vx, vy in front_verts:
                y_key = round(vy, 1)
                if y_key not in y_groups:
                    y_groups[y_key] = []
                y_groups[y_key].append((idx, vx))

            # Find Y levels with exactly 2 vertices (left/right edges of a step)
            width_dims_added = 0
            for y_key in sorted(y_groups.keys()):
                verts_at_y = y_groups[y_key]
                if len(verts_at_y) >= 2:
                    verts_at_y.sort(key=lambda v: v[1])
                    width = abs(verts_at_y[-1][1] - verts_at_y[0][1])
                    if width > 2.0:  # skip tiny features
                        add_dim(doc, page, front, "DistanceX",
                                (f"Vertex{verts_at_y[0][0]}",
                                 f"Vertex{verts_at_y[-1][0]}"),
                                y_off=8 + width_dims_added * 7,
                                name_prefix="DimPostW")
                        width_dims_added += 1
                        if width_dims_added >= 2:
                            break

    if right:
        circles = get_circles(right)
        if circles:
            radii = find_unique_radii(circles)
            y_offset = -5
            for r, cs in sorted(radii.items(), reverse=True):
                if r < 0.5:
                    continue
                add_dim(doc, page, right, "Diameter",
                        (f"Edge{cs[0][0]}",),
                        x_off=8, y_off=y_offset, name_prefix="DimPostD")
                y_offset += 10


# ============================================================
# WHEEL
# ============================================================

def create_wheel_drawing(doc, page, obj):
    """Create wheel drawing: face view + side profile."""
    group = doc.addObject("TechDraw::DrawProjGroup", "ProjGroup")
    page.addView(group)

    group.Source = [obj]
    group.ProjectionType = "Third Angle"
    group.ScaleType = "Custom"
    group.Scale = 5.0

    # Front = face view (showing teeth)
    group.addProjection("Front")
    group.Anchor.Direction = App.Vector(0, 0, 1)
    group.Anchor.XDirection = App.Vector(1, 0, 0)

    # Right = side profile (showing tooth width)
    group.addProjection("Right")

    # Position: left of center to leave room for right projection
    group.X = 90
    group.Y = 90

    doc.recompute()
    process_events(8)
    doc.recompute()

    return group, None


def add_wheel_dimensions(doc, page):
    """Add dimensions to wheel drawing."""
    items = find_view_items(doc)
    front = items.get("Front")
    right = items.get("Right")

    if front:
        circles = get_circles(front)
        if circles:
            radii = find_unique_radii(circles)
            # Only dimension the largest (tip) and smallest significant (bore)
            sig_radii = {r: cs for r, cs in radii.items() if r >= 0.5}
            sorted_r = sorted(sig_radii.items())

            if sorted_r:
                # Tip diameter (largest)
                r_tip, cs_tip = sorted_r[-1]
                add_dim(doc, page, front, "Diameter",
                        (f"Edge{cs_tip[0][0]}",),
                        x_off=8, y_off=-8, name_prefix="DimWTip")

            if len(sorted_r) >= 2:
                # Bore diameter (smallest)
                r_bore, cs_bore = sorted_r[0]
                add_dim(doc, page, front, "Diameter",
                        (f"Edge{cs_bore[0][0]}",),
                        x_off=-8, y_off=8, name_prefix="DimWBore")

    if right:
        right_verts = get_vertices(right)
        if right_verts:
            xs = [v[1] for v in right_verts]
            ys = [v[2] for v in right_verts]
            # Face width
            v_l = find_vertex_near(right_verts, min(xs), 0,
                                   tol=abs(max(ys)) + 1)
            v_r = find_vertex_near(right_verts, max(xs), 0,
                                   tol=abs(max(ys)) + 1)
            if v_l is not None and v_r is not None and v_l != v_r:
                add_dim(doc, page, right, "DistanceX",
                        (f"Vertex{v_l}", f"Vertex{v_r}"),
                        y_off=12, name_prefix="DimFaceW")


# ============================================================
# PEG HEAD
# ============================================================

def create_peg_head_drawing(doc, page, obj):
    """Create peg head drawing: side profile + top view + end view."""
    group = doc.addObject("TechDraw::DrawProjGroup", "ProjGroup")
    page.addView(group)

    group.Source = [obj]
    group.ProjectionType = "Third Angle"
    group.ScaleType = "Custom"
    group.Scale = 3.0

    # Front = side profile (shows worm + shaft)
    group.addProjection("Front")
    group.Anchor.Direction = App.Vector(0, -1, 0)
    group.Anchor.XDirection = App.Vector(1, 0, 0)

    # Right = end view (circular cross-section)
    group.addProjection("Right")
    # Top = top view
    group.addProjection("Top")

    # Position: center-left, with room for right and top projections
    group.X = 100
    group.Y = 105

    doc.recompute()
    process_events(8)
    doc.recompute()

    return group, None


def add_peg_head_dimensions(doc, page):
    """Add dimensions to peg head drawing."""
    items = find_view_items(doc)
    front = items.get("Front")
    right = items.get("Right")

    if front:
        front_verts = get_vertices(front)
        if front_verts:
            xs = [v[1] for v in front_verts]
            ys = [v[2] for v in front_verts]

            # Overall length
            v_left = find_vertex_near(front_verts, min(xs), min(ys))
            v_right = find_vertex_near(front_verts, max(xs), min(ys))
            if v_left is not None and v_right is not None and v_left != v_right:
                add_dim(doc, page, front, "DistanceX",
                        (f"Vertex{v_left}", f"Vertex{v_right}"),
                        y_off=12, name_prefix="DimPegLen")

    if right:
        circles = get_circles(right)
        if circles:
            radii = find_unique_radii(circles)
            sig_radii = {r: cs for r, cs in radii.items() if r >= 0.3}
            sorted_r = sorted(sig_radii.items())

            # Dimension largest and smallest significant circles
            offsets = [(8, -8), (-8, 8), (10, 0)]
            for i, (r, cs) in enumerate(sorted_r):
                if i >= len(offsets):
                    break
                x_off, y_off = offsets[i]
                add_dim(doc, page, right, "Diameter",
                        (f"Edge{cs[0][0]}",),
                        x_off=x_off, y_off=y_off,
                        name_prefix="DimPegD")


# ============================================================
# Dispatch tables
# ============================================================

COMPONENT_CREATORS = {
    "frame": create_frame_drawing,
    "string_post": create_string_post_drawing,
    "wheel": create_wheel_drawing,
    "peg_head": create_peg_head_drawing,
}

DIMENSION_ADDERS = {
    "frame": add_frame_dimensions,
    "string_post": add_string_post_dimensions,
    "wheel": add_wheel_dimensions,
    "peg_head": add_peg_head_dimensions,
}

SCALE_TEXT = {
    "frame": "1:1",
    "string_post": "5:1",
    "wheel": "5:1",
    "peg_head": "3:1",
}


# ============================================================
# Main
# ============================================================

def main():
    """Main entry point."""
    step_file = os.environ.get("DRAWING_STEP_FILE", "")
    output_dir = os.environ.get("DRAWING_OUTPUT_DIR", "drawings")
    component = os.environ.get("DRAWING_COMPONENT", "frame")
    title = os.environ.get(
        "DRAWING_TITLE",
        f"Parametric {component.replace('_', ' ').title()}")
    hand = os.environ.get("DRAWING_HAND", "rh")
    gear = os.environ.get("DRAWING_GEAR", "")

    if not step_file:
        print("ERROR: DRAWING_STEP_FILE not set")
        Gui.getMainWindow().close()
        return

    step_file = os.path.abspath(step_file)
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Component: {component}")
    print(f"STEP: {step_file}")
    print(f"Output: {output_dir}")

    # Create document and import STEP
    doc = App.newDocument("Drawing")
    obj = doc.addObject("Part::Feature", component.title())
    obj.Shape = Part.read(step_file)
    doc.recompute()

    bb = obj.Shape.BoundBox
    print(f"Bounding box: [{bb.XMin:.1f},{bb.XMax:.1f}] x "
          f"[{bb.YMin:.1f},{bb.YMax:.1f}] x [{bb.ZMin:.1f},{bb.ZMax:.1f}]")

    # Create page
    page, tpl = create_page(doc)
    scale_text = SCALE_TEXT.get(component, "1:1")
    fill_title_block(tpl, title, gear=gear, scale_text=scale_text)

    # Create views
    creator = COMPONENT_CREATORS.get(component)
    if not creator:
        print(f"ERROR: Unknown component '{component}'")
        Gui.getMainWindow().close()
        return

    group, iso = creator(doc, page, obj)

    # Recompute views
    doc.recompute()
    process_events(3)
    doc.recompute()

    # Add dimensions
    dim_adder = DIMENSION_ADDERS.get(component)
    if dim_adder:
        try:
            dim_adder(doc, page)
            print("Dimensions added")
        except Exception as e:
            print(f"Dimension error: {e}")

    # Final recompute
    doc.recompute()
    process_events(2)
    doc.recompute()

    # Open TechDraw page in MDI view to force dimension rendering
    try:
        page.ViewObject.doubleClicked()
    except Exception:
        pass
    process_events(5)
    try:
        Gui.runCommand("TechDraw_RedrawPage")
    except Exception:
        pass
    process_events(3)
    doc.recompute()

    # Export
    basename = f"{component}_{hand}" if hand else component
    import TechDrawGui

    fcstd_path = os.path.join(output_dir, f"{basename}.FCStd")
    doc.saveAs(fcstd_path)
    print(f"FCStd: {fcstd_path}")

    svg_path = os.path.join(output_dir, f"{basename}.svg")
    TechDrawGui.exportPageAsSvg(page, svg_path)
    print(f"SVG: {svg_path} ({os.path.getsize(svg_path)} bytes)")

    pdf_path = os.path.join(output_dir, f"{basename}.pdf")
    TechDrawGui.exportPageAsPdf(page, pdf_path)
    print(f"PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")

    status_path = os.path.join(output_dir, f".drawing_status_{basename}")
    with open(status_path, "w") as f:
        f.write("DONE\n")
        f.write(f"fcstd={fcstd_path}\n")
        f.write(f"svg={svg_path}\n")
        f.write(f"pdf={pdf_path}\n")

    print("DONE")
    sys.stdout.flush()

    try:
        App.closeDocument(doc.Name)
    except Exception:
        pass
    os._exit(0)


# Run
main()
