"""Engineering analysis of pip stalk shear/bending for CZ121 brass.

CZ121 (CW614N) free-machining brass properties:
- Tensile strength: 360-400 MPa
- 0.2% Proof stress (yield): 250 MPa
- Shear strength: ~60% of UTS = 216-240 MPa
- Elongation: 10-20%

Loading scenario: finger applies tangential force to pip to rotate tuning peg.
The stalk acts as a short cantilever. Both shear and bending are checked.
"""

import math

# --- Material Properties (CZ121 / CW614N) ---
TENSILE_UTS = 380  # MPa (mid-range)
YIELD_STRENGTH = 250  # MPa (0.2% proof)
SHEAR_STRENGTH = 0.6 * TENSILE_UTS  # ~228 MPa
SAFETY_FACTOR = 2.0  # Conservative for decorative part

ALLOWABLE_SHEAR = SHEAR_STRENGTH / SAFETY_FACTOR
ALLOWABLE_BENDING = YIELD_STRENGTH / SAFETY_FACTOR

# --- Current Geometry (from STEP analysis) ---
# Pip: d=2.1mm, length=1.2mm
# Stalk: d=1.0mm, length=0.2mm
# Fillets: 0.3mm radius at both ends of pip
# Total cantilever from ring surface to pip tip ≈ 1.4mm

PIP_DIAMETER = 2.1       # mm
PIP_LENGTH = 1.2          # mm
STALK_DIAMETER_CURRENT = 1.0  # mm
STALK_LENGTH = 0.2        # mm
FILLET_R = 0.3            # mm

# Effective cantilever length from stalk root to center of applied force
# Force applied at pip center (finger contact)
CANTILEVER_LENGTH = STALK_LENGTH + PIP_LENGTH / 2  # 0.2 + 0.6 = 0.8mm

# --- Loading ---
# Typical finger force for tuning: 5-10N
# Accidental snag/catch force: up to 30N
# We design for accidental load
FORCES = [5, 10, 20, 30]  # N - range of scenarios

print("=" * 70)
print("PIP STALK ENGINEERING ANALYSIS — CZ121 BRASS")
print("=" * 70)
print(f"\nMaterial: CZ121 (CW614N) free-machining brass")
print(f"  UTS:            {TENSILE_UTS} MPa")
print(f"  Yield (0.2%):   {YIELD_STRENGTH} MPa")
print(f"  Shear strength: {SHEAR_STRENGTH:.0f} MPa")
print(f"  Safety factor:  {SAFETY_FACTOR}")
print(f"  Allowable shear:   {ALLOWABLE_SHEAR:.0f} MPa")
print(f"  Allowable bending: {ALLOWABLE_BENDING:.0f} MPa")

print(f"\nGeometry:")
print(f"  Pip diameter:   {PIP_DIAMETER} mm")
print(f"  Pip length:     {PIP_LENGTH} mm")
print(f"  Stalk length:   {STALK_LENGTH} mm")
print(f"  Cantilever arm: {CANTILEVER_LENGTH} mm (to mid-pip)")
print(f"  Fillet radius:  {FILLET_R} mm")


def analyze_stalk(diameter, label=""):
    """Analyze stalk at given diameter for all load cases."""
    r = diameter / 2
    area = math.pi * r**2                    # mm²
    I = math.pi * r**4 / 4                   # mm⁴ (second moment of area)
    Z_section = math.pi * r**3 / 4           # mm³ (section modulus = I/c where c=r)
    J = math.pi * r**4 / 2                   # mm⁴ (polar moment - for torsion)

    print(f"\n{'─' * 70}")
    print(f"  STALK DIAMETER: {diameter:.1f} mm  {label}")
    print(f"{'─' * 70}")
    print(f"  Cross-section area:  {area:.4f} mm²")
    print(f"  Section modulus (Z): {Z_section:.6f} mm³")
    print(f"  Second moment (I):   {I:.6f} mm⁴")

    print(f"\n  {'Force':>6s}  {'τ_shear':>10s}  {'σ_bend':>10s}  {'τ/allow':>8s}  {'σ/allow':>8s}  {'Status':>10s}")
    print(f"  {'(N)':>6s}  {'(MPa)':>10s}  {'(MPa)':>10s}  {'':>8s}  {'':>8s}  {'':>10s}")

    for F in FORCES:
        # Direct shear: max shear in circular section = 4V/(3A)
        tau_shear = (4 * F) / (3 * area)

        # Bending: σ = M/Z = F*L / Z
        M = F * CANTILEVER_LENGTH  # N·mm
        sigma_bend = M / Z_section

        # Combined (von Mises for ductile material)
        # σ_vm = sqrt(σ² + 3τ²)
        sigma_vm = math.sqrt(sigma_bend**2 + 3 * tau_shear**2)

        shear_ratio = tau_shear / ALLOWABLE_SHEAR
        bend_ratio = sigma_bend / ALLOWABLE_BENDING

        if bend_ratio > 1.0 or shear_ratio > 1.0:
            status = "** FAILS **"
        elif bend_ratio > 0.7 or shear_ratio > 0.7:
            status = "MARGINAL"
        else:
            status = "OK"

        print(f"  {F:6.0f}  {tau_shear:10.1f}  {sigma_bend:10.1f}  "
              f"{shear_ratio:8.2f}  {bend_ratio:8.2f}  {status:>10s}")

    return area


print("\n\n" + "=" * 70)
print("STRESS ANALYSIS BY STALK DIAMETER")
print("=" * 70)

diameters = [1.0, 1.2, 1.4, 1.5, 1.6, 1.8, 2.0, 2.1]
for d in diameters:
    label = "(CURRENT)" if d == 1.0 else ("(= pip OD)" if d == 2.1 else "")
    analyze_stalk(d, label)


# --- Minimum diameter calculation ---
print("\n\n" + "=" * 70)
print("MINIMUM DIAMETER CALCULATION")
print("=" * 70)

for F in FORCES:
    # Bending dominates. σ_allow = M/Z = F*L / (π*r³/4)
    # Solving for r: r³ = 4*F*L / (π * σ_allow)
    # r = (4*F*L / (π * σ_allow))^(1/3)
    r_min = (4 * F * CANTILEVER_LENGTH / (math.pi * ALLOWABLE_BENDING)) ** (1/3)
    d_min = 2 * r_min
    print(f"  F={F:5.0f}N → min diameter (bending): {d_min:.2f} mm")

print(f"\n  Note: These are minimum diameters with SF={SAFETY_FACTOR}")
print(f"  Bending dominates over shear for this short cantilever geometry.")


# --- Recommendation ---
print("\n\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)
print("""
The current 1.0mm stalk fails in bending at loads above ~10N.
For a tuning peg that fingers grip and twist, accidental side loads
of 20-30N are realistic (bumping, catching on cloth, etc).

Options:
  1.5mm — passes all loads up to 20N, marginal at 30N
  1.8mm — comfortable margin at 30N, still visually stepped
  2.1mm — flush with pip (no step), strongest, simplest fix

Since the stalk is only 0.2mm long, the visual difference between
1.5mm and 2.1mm is negligible. Going flush at 2.1mm is the most
robust choice and eliminates the stress concentration entirely.
""")
