# Stability check

## Status

| Check | Result |
|---|---|
| Hand calculation (`sizing/report.md`, section 5) | Neutral point 41.6% chord, static margin **14.6%** at the 27% design CG, 16.6% at the 25% first-flight CG |
| XFLR5 | **Not run yet.** This has to be done on a computer with XFLR5 installed. The inputs below are ready. |

The hand calculation uses the tail volume coefficient, finite-wing lift slopes and a
simple downwash estimate. It is usually within a few percent of chord, which is why it
needs the XFLR5 check before the full plane is built.

## Inputs for XFLR5

Units: mm and grams. Values are the defaults; if `params.py` changes, read the new ones
from `sizing/design.json`.

**Airfoils**
- Wing: load `analysis/clarky.dat` (File > Open). Refine globally to about 100 panels.
- Tail: NACA 0006 or a flat plate (Design > Naca Foils > 0006).
- Direct analysis: batch-analyse both foils, Type 1, Reynolds 60 000 to 300 000 in steps of 20 000, alpha -5° to 12°.

**Main wing** (Plane > Define a new plane)

| Field | Value |
|---|---|
| Span | 1000 |
| Root and tip chord | 200 |
| Offset | 0 |
| Dihedral | 4° |
| Twist | 0 |
| Incidence | 2° (the flat bottom sits on the fuselage top; the Clark Y chord line is about 2° nose-up from the flat bottom) |
| Position | x = 0, z = 0 |

**Elevator (horizontal tail)**

| Field | Value |
|---|---|
| Span | 374 |
| Chord | 107 |
| Incidence | 0° |
| Position x (leading edge behind the wing leading edge) | 523 |
| Position z | 0 |

**Fin**

| Field | Value |
|---|---|
| Height | 150 |
| Root / tip chord | 133 / 80 |
| Tip offset | 53 |
| Position x | 507 |

**Mass** (Plane > Define inertia): total 783 g, CG at x = 54 mm behind the wing leading
edge (27% chord). For the first-flight case use x = 50 mm.

## What to run

1. Analysis > Define an analysis: Type 2 (fixed lift), Ring vortex (VLM2), viscous on, plane mass 0.783 kg.
2. Sweep alpha from -4° to 10°.
3. Read off:
   - **Neutral point** `XNP` (shown in the plane properties after the analysis).
   - **Cm vs alpha**: the slope must be negative.
   - **Trim point**: the alpha where Cm = 0, and the speed there.
4. Static margin = (XNP − XCG) / 200.

## Results (fill in)

| Quantity | Hand estimate | XFLR5 |
|---|---|---|
| Neutral point behind the wing leading edge | 83 mm (41.6%) | |
| Static margin at CG = 54 mm | 14.6% | |
| Static margin at CG = 50 mm | 16.6% | |
| Cm-alpha slope | negative | |
| Trim speed | about 12 m/s | |

## If it does not pass

- **Margin below 10%:** move the CG forward (slide the battery), or raise `VH` in `params.py` and rebuild.
- **Margin above about 18%:** the plane will feel nose-heavy and need a lot of up elevator. Move the CG back in small steps (5 mm at a time) between flights, never past 30% chord.
- **Trim needs a lot of elevator:** shim the wing trailing edge or leading edge by 1–2 mm to change the incidence.
