#!/usr/bin/env python3
"""General arrangement of the full 5-gang tuner assembly (RH).

Thin wrapper around ``draftwright.make_drawing()``: it builds the production
5-gang assembly (the same ``create_positioned_assembly()`` path as build.py /
viz.py, so positions cannot drift) and hands it to draftwright, which lays out
the views, picks the scale/page, dimensions the geometry and adds the hole
callouts automatically.

Outputs: drawings/<gear>/assembly_ga5_rh.svg / .dxf
The combined PDF pack is assembled separately by scripts/drawings/make_pdf.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from build123d import Compound
from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.assembly.gang_assembly import create_positioned_assembly
from draftwright import make_drawing

GEAR    = 'c13-10'
OUT_DIR = Path(__file__).parent.parent / 'drawings' / GEAR
OUT_DIR.mkdir(parents=True, exist_ok=True)
STEM    = OUT_DIR / 'assembly_ga5_rh'

gp  = resolve_gear_config(GEAR)
cfg = create_default_config(gear_json_path=gp.json_path, config_dir=gp.config_dir)

print('Building 5-gang assembly...')
asm   = create_positioned_assembly(cfg, wheel_step_path=gp.wheel_step,
                                   worm_step_path=gp.worm_step)
whole = Compound(children=list(asm['all_parts'].values()))

print('Generating drawing (draftwright)...')
svg, dxf = make_drawing(
    whole,
    out=str(STEM),
    title='GENERAL ARRANGEMENT — 5-GANG (RH)',
    number='GIB-TUN-GA5-RH',
    tolerance='ISO 2768-f',
    drawn_by='P. Fremantle',
    page='A3',   # match the rest of the drawing pack (make_pdf assumes <=A3)
)
print(f'Wrote {svg}\n      {dxf}')
