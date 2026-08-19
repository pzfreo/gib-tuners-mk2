# Production Build Guide

This document records exactly how to generate the CNC files for the 5-gang tuning machine assembly.

## Build Command

```bash
python scripts/build.py --hand both --gear c13-10 -n 5 --label-frames no
```

| Flag | Value | Reason |
|------|-------|--------|
| `--hand both` | RH + LH | Generate both variants in one run |
| `--gear c13-10` | c13-10 | Production gear profile (M0.5, 13-tooth, cylindrical worm) |
| `-n 5` | 5 housings | Full 5-gang assembly, 145mm frame |
| `--label-frames no` | No label etch | Omit L/R etch; with labels on, RH and RH frames differ in size |

Output goes to `output/` by default (STEP + STL for each component).

## Output Files

| File | Description |
|------|-------------|
| `frame_rh_5gang.step` | Right-hand frame |
| `frame_lh_5gang.step` | Left-hand frame (mirror of RH — must be same file size) |
| `peg_head_rh.step` | Right-hand peg head with worm |
| `peg_head_lh.step` | Left-hand peg head (mirrored, left-hand worm helix) |
| `string_post.step` | String post (symmetric — one file for both hands) |
| `wheel_rh.step` | Right-hand worm wheel |
| `wheel_lh.step` | Left-hand worm wheel (mirrored) |

## Validation Before Sending

Run `scripts/check_production.py` to confirm the new build contains exactly the expected changes:

```bash
# After building to output/:
python scripts/check_production.py

# Or against a specific directory:
python scripts/check_production.py --baseline sent/ptype/ --new sent/fixedv2/
```

The script checks each component against the `sent/ptype/` baseline:

| Component | Check |
|-----------|-------|
| frame LH + RH | Identical file sizes (labels off), mounting holes ≈ 3.2mm, volume/bbox unchanged |
| string_post | String hole ≈ 1.7mm, chamfer faces present, volume/bbox unchanged |
| peg_head LH + RH | Pip stalk ≥ 1.4mm (reinforced), volume/bbox unchanged |

Expected output: `RESULT: PASS — all checks passed`

## Gear Profile: c13-10

Located in `config/c13-10/`. Key parameters:

| Parameter | Value |
|-----------|-------|
| Gear module | M0.5 |
| Worm starts | 1 |
| Wheel teeth | 13 |
| Ratio | 13:1 |
| Pressure angle | 20° |
| Centre distance | 6.25mm |
| Worm type | Cylindrical (ZI) |
| Worm tip diameter | 7.0mm |
| Worm root diameter | 4.75mm |
| Wheel tip diameter | 7.6mm |
| Wheel bore | 3.5mm (DD cut) |
| Peg shaft diameter | 4.5mm (overridden in `tuner_config.json`) |
| Frame wall thickness | 1.0mm (overridden in `tuner_config.json`) |

## What Changed Since First Prototype Send (sent/ptype, Feb 2026)

| Change | Commit | Effect on files |
|--------|--------|-----------------|
| Pip stalk reinforcement 1.0mm → 1.5mm | PR #76 | `peg_head_*.step` slightly larger |
| String hole 1.5mm → 1.7mm + chamfers | PR (Mar 2026) | `string_post.step` larger |
| Mounting holes 3.0mm → 3.2mm | PR (Mar 2026) | `frame_*.step` slightly changed |

## Cutting a Release

`.github/workflows/release.yml` packages the production geometry and the drawing
suite into a GitHub release. Push a version tag to run it:

```bash
git tag -a v0.2.1 -m "Production pack"
git push origin v0.2.1
```

The workflow runs the test suite, then in parallel:

| Job | Does |
|-----|------|
| `build` | Production build (STEP + STL), then `check_production.py` against the `sent/ptype` baseline |
| `drawings` | The 5 A3 sheets + `tuner_drawings.pdf` + `drawings_dxf_svg.zip` |
| `release` | Flattens both artifact sets and creates the release (24 assets) |

The release is created as a **draft** so the notes can be reviewed first. Publish it with:

```bash
gh release edit v0.2.1 --draft=false
```

Boilerplate notes live in `.github/release-notes.md`; `--generate-notes` appends
the commit/PR list since the previous tag. To publish automatically instead, drop
the `--draft` flag from the workflow's final step.

`workflow_dispatch` runs the same build and validation from any branch but skips
the release step — use it to dry-run the asset pack before tagging.

The workflow warns (but does not fail) if the tag does not match `version` in
`pyproject.toml`, so bump that in the release commit.
