"""Combine all engineering drawing SVGs into a single multi-page PDF.

Rasterises each SVG to PNG at 200 DPI (2339×1654 px) using resvg-py,
then assembles pages into an A4 landscape PDF via fpdf2.

Page order:
    DWG-001  frame.svg
    DWG-002  string_post.svg
    DWG-003  peg_head.svg
    DWG-004  assembly.svg
    DWG-005  worm_wheel.svg

Run:
    uv run python scripts/drawings/make_pdf.py
Output:
    drawings/tuner_drawings.pdf
"""

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import resvg_py
from fpdf import FPDF

DRAWINGS_DIR = Path(__file__).parent.parent.parent / "drawings"

PAGES = [
    "frame.svg",
    "string_post.svg",
    "peg_head.svg",
    "assembly.svg",
    "worm_wheel.svg",
]

PAGE_W_MM = 297.0   # A4 landscape
PAGE_H_MM = 210.0


def _parse_svg_geometry(svg_path: Path):
    """Return (pdf_x, pdf_y, w_mm, h_mm) for placing the SVG on an A4 landscape page.

    build123d ExportSVG writes SVG with Y-up coords; the viewBox encodes where
    the content sits on the A4 sheet.  We recover the PDF (Y-down, top-left origin)
    placement by inverting the Y axis.
    """
    ns = {"svg": "http://www.w3.org/2000/svg"}
    tree = ET.parse(str(svg_path))
    root = tree.getroot()

    # Strip namespace if present
    vb_str = root.get("viewBox", "0 0 297 210")
    vb = [float(v) for v in vb_str.split()]
    vb_x, vb_y, vb_w, vb_h = vb

    # width / height in mm
    def _to_mm(s: str) -> float:
        return float(s.replace("mm", "").strip())

    w_mm = _to_mm(root.get("width", f"{vb_w}mm"))
    h_mm = _to_mm(root.get("height", f"{vb_h}mm"))

    # build123d uses Y-up.  After the implicit SVG Y-flip:
    #   SVG viewBox top-left y = vb_y  (negative in drawing coords)
    #   Drawing top of content = abs(vb_y)          (Y measured from page bottom)
    #   PDF Y (top-down)       = PAGE_H_MM - abs(vb_y)
    pdf_x = vb_x
    pdf_y = PAGE_H_MM - abs(vb_y)
    return pdf_x, pdf_y, w_mm, h_mm


def svg_to_png(svg_path: Path) -> bytes:
    """Rasterise SVG → PNG bytes at 200 DPI."""
    return resvg_py.svg_to_bytes(svg_path=str(svg_path), dpi=200)


def make_pdf(output_path: Path) -> None:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)

    added = 0
    for svg_name in PAGES:
        svg_path = DRAWINGS_DIR / svg_name
        if not svg_path.exists():
            print(f"  SKIP {svg_name} — not found")
            continue
        print(f"  Rasterising {svg_name} …", end="", flush=True)
        png_bytes = svg_to_png(svg_path)
        print(f" {len(png_bytes)//1024} KB")
        pdf_x, pdf_y, w_mm, h_mm = _parse_svg_geometry(svg_path)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(png_bytes)
            tmp_path = tmp.name

        pdf.add_page()
        pdf.image(tmp_path, x=pdf_x, y=pdf_y, w=w_mm, h=h_mm)
        Path(tmp_path).unlink(missing_ok=True)
        print(f"  Page {pdf.page}: {svg_name}  ({pdf_x:.1f}, {pdf_y:.1f}) {w_mm:.1f}×{h_mm:.1f}mm")
        added += 1

    if added == 0:
        print("No SVG files found — no PDF written.")
        return

    pdf.output(str(output_path))
    size_kb = output_path.stat().st_size // 1024
    print(f"\nPDF: {output_path}  ({size_kb} KB, {added} pages)")


if __name__ == "__main__":
    output = DRAWINGS_DIR / "tuner_drawings.pdf"
    DRAWINGS_DIR.mkdir(exist_ok=True)
    make_pdf(output)
