Parametric CAD outputs for the 5-gang tuning machine, gear profile `c13-10`
(cylindrical worm, M0.5, 13-tooth wheel, 20° pressure angle, 6.25mm centre distance).

Built with:

```
python scripts/build.py --hand both --gear c13-10 -n 5 --label-frames no --format both
```

Validated against the `sent/ptype` baseline by `scripts/check_production.py`.

## Artifacts

**Assemblies** (all parts positioned)
- `assembly_5gang_rh.step` / `assembly_5gang_lh.step`
- `assembly_5gang.glb` — coloured, for 3D viewers

**Components** (STEP + STL)
- Frame RH/LH, 5-gang, unlabelled for CNC
- String post (symmetric — one part for both hands)
- Peg head RH/LH
- Wheel RH/LH

**Engineering drawings** (A3, RH shown — LH is the mirror image)
- `tuner_drawings.pdf` — all 5 sheets
- Per-sheet PDFs, plus `drawings_dxf_svg.zip` with the DXF/SVG sources

All dimensions 1:1 scale, production tolerance.
