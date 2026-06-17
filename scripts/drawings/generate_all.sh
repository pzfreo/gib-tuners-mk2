#!/usr/bin/env bash
# Generate every engineering drawing sheet and assemble the combined PDF pack.
#
# Single source of truth for the drawing set, shared by CI (.github/workflows/
# ci.yml) and the release workflow (.github/workflows/release.yml) so the two
# cannot drift — add a new sheet here and both pipelines pick it up.
#
# pyvista renders the shaded pictorials off-screen; callers on headless runners
# must provide a virtual display (see pyvista/setup-headless-display-action).
set -euo pipefail
cd "$(dirname "$0")/../.."

python scripts/frame_drawing.py
python scripts/string_post_drawing.py
python scripts/peg_head_drawing.py
python scripts/wheel_drawing.py
python scripts/assembly_drawing.py
python scripts/assembly_5gang_drawing.py

python scripts/drawings/make_pdf.py
