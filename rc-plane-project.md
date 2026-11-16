# Project: Self-Designed RC Trainer Plane

**Student:** Arslan Xajiyev (grade 9)
**Goal:** Design, build and fly an electric RC plane designed from first principles. Every key dimension comes from a calculation, not a kit.

This file is a design brief for Claude Code. Build the project as parametric CAD plus a design calculator, so that changing one input (for example the wingspan) updates the whole plane.

---

## 1. Tools and output

- **CAD:** CadQuery (Python).
- **Language:** Python 3 for sizing, CAD and analysis.
- **Outputs:** A sizing report, STL files for 3D-printed parts, flat templates (SVG/PDF) for foam-board parts, and a build guide.
- **Construction approach:** Hybrid.
  - **Foam board** (5 mm, paper-faced, e.g. "Dollar Tree" style or local equivalent): wing skins, fuselage box, tail surfaces. Light, cheap, easy to repair.
  - **3D-printed PLA or LW-PLA:** motor mount, firewall, wing-root joiners, servo mounts, control horns, landing-gear mounts, nose cone.
- **Printer constraints (edit to match the school printer):** 220 × 220 × 250 mm build volume, 0.4 mm nozzle.

### Suggested repository layout

```
rc-plane/
├── params.py               # inputs: wingspan, airfoil, weight target, etc.
├── sizing/
│   └── design_calc.py      # derives all dimensions and prints a report
├── cad/
│   ├── wing.py             # rib profiles + spar slots, foam template
│   ├── fuselage.py
│   ├── tail.py
│   ├── printed_parts.py    # motor mount, servo mounts, horns, joiners
│   └── export_templates.py # SVG/PDF cut templates at 1:1 scale
├── stl/
├── templates/
├── analysis/
│   └── xflr5_notes.md      # stability check results
└── README.md
```

---

## 2. Design targets (starting point, all in `params.py`)

| Parameter | Starting value | Reason |
|---|---|---|
| Layout | High-wing, conventional tail, tractor motor | Stable and forgiving trainer |
| Wingspan | 1000 mm | Big enough to see, small enough to transport |
| Chord | 200 mm (constant) | Aspect ratio ≈ 5, simple to build |
| Airfoil | Clark Y (or flat-bottom KFm-style for foam) | Gentle stall, flat bottom eases building |
| Dihedral | 3–5° | Roll stability |
| Controls | Aileron, elevator, rudder, throttle (4 channels) | |
| All-up weight target | 700–900 g | |
| Wing loading target | 30–45 g/dm² | Slow, docile flight |
| Thrust-to-weight | ≥ 0.8 | Easy climb-out |

---

## 3. Sizing calculator (`sizing/design_calc.py`)

The script takes the inputs above and prints:

1. **Wing area** `S = b · c` and **aspect ratio** `AR = b² / S`.
2. **Wing loading** = weight / area in g/dm². Warn if it falls outside 30–45.
3. **Stall speed:** `V_stall = sqrt(2W / (ρ · S · C_Lmax))`, with C_Lmax ≈ 1.1 for Clark Y at low Reynolds number. Target under 9 m/s.
4. **Fuselage length** ≈ 70–75% of the wingspan.
5. **Tail moment arm** `L_t`: distance from the wing's quarter-chord to the tail's quarter-chord, ≈ 2.5–3 × chord.
6. **Horizontal tail area** from the tail volume coefficient:
   `S_h = V_h · S · c / L_t`, with `V_h` = 0.45–0.55.
7. **Vertical tail area:** `S_v = V_v · S · b / L_t`, with `V_v` = 0.035–0.045.
8. **Control surface sizes:** ailerons ≈ 20–25% of chord over the outer 40–50% of each half-span; elevator ≈ 30–40% of the horizontal tail chord; rudder ≈ 30–40% of the fin chord.
9. **Center of gravity (CG):** 25–30% of the chord from the leading edge. Start at 25%.
10. **Weight budget table:** sum of all components vs target, with a warning if over.
11. **Power estimate:** about 150–200 W/kg for a trainer, so roughly 120–180 W for this plane.

All derived values should be written to a JSON file that the CAD scripts read, so the geometry always matches the calculation.

---

## 4. Electronics (typical trainer setup, check local availability)

| Component | Spec |
|---|---|
| Motor | 2212 brushless, ~1000–1400 KV |
| ESC | 30 A with BEC |
| Propeller | 8×4 to 10×4.7 (match to motor KV and battery) |
| Battery | 3S LiPo, 1300–2200 mAh |
| Servos | 4 × 9 g micro servos (2 aileron, 1 elevator, 1 rudder) |
| Radio | Any 4+ channel transmitter and matching receiver |
| Pushrods | 1–1.5 mm steel wire or carbon rod with Z-bends / clevises |

**Optional for Otabek's side:** a flight logger (Arduino Nano + MPU6050 IMU + BMP280 barometer + SD card) recording attitude and altitude. This turns the plane into a joint project.

---

## 5. CAD requirements

### Wing (`cad/wing.py`)
- Generate the airfoil profile from coordinates and output a 1:1 template for cutting foam, plus a folded-wing ("KF" or "FT-style") option.
- Spar slot for a carbon tube or wooden dowel at ~25–30% chord.
- Split into two halves, joined by a printed center joiner that sets the dihedral angle.
- Aileron hinge lines and servo pocket cutouts marked.

### Fuselage (`cad/fuselage.py`)
- Box fuselage from foam board, with fold lines on the template.
- Battery bay placed so that moving the battery can adjust the CG.
- Wing attached with rubber bands or nylon bolts so it can come off in a crash.

### Tail (`cad/tail.py`)
- Horizontal and vertical tail from 5 mm foam, sized from the calculator.
- Hinge lines and control-horn positions marked.

### Printed parts (`cad/printed_parts.py`)
- Motor mount with 2–3° right thrust and 1–2° down thrust (adjustable params).
- Firewall plate, servo mounts sized for 9 g servos, control horns, wing joiner, landing-gear block.
- Every part fits the printer bed; walls ≥ 1.2 mm; holes sized for M3 hardware.

---

## 6. Stability check (before building)

1. Model the plane in XFLR5 using the calculator's dimensions.
2. Check the **static margin**: aim for 10–15% of the mean aerodynamic chord.
3. Confirm the neutral point is behind the CG.
4. Record results in `analysis/xflr5_notes.md`. If unstable, adjust tail area or CG and rerun the calculator.

---

## 7. Build and test plan

1. Print and cut a **half-scale glider** (no motor) from the same scripts and hand-launch it to check balance and glide.
2. Build the full plane; check the CG on fingertips at the marked position.
3. Range-test the radio and check all control directions (the most common first-flight mistake is a reversed control).
4. Set control throws: start small (aileron ±10 mm, elevator ±8 mm, rudder ±15 mm at the trailing edge).
5. First flight with an experienced RC pilot on the sticks or on a buddy-box if possible, over grass, in calm wind.
6. Log flights: battery used, flight time, what happened, what to change.

---

## 8. Safety

- **Propeller:** Never install the prop while working on the plane with the battery connected.
- **LiPo batteries:** Charge only with a balance charger, in a LiPo-safe bag, never unattended. Do not use a puffed or damaged battery.
- **Flying site:** Open field away from people, buildings, roads and power lines, ideally with an RC club. Check current rules on model aircraft and drone flying in Uzbekistan before flying, and stay well away from airports and restricted areas.
- **Supervision:** A teacher or adult present for all flights.

---

## 9. Acceptance criteria

- [ ] Changing `params.py` and rerunning the scripts updates every dimension, template and STL
- [ ] The sizing report shows wing loading, stall speed, tail volumes and CG position
- [ ] Weight budget is within target
- [ ] XFLR5 confirms a positive static margin of 10–15%
- [ ] All printed parts fit the printer
- [ ] 1:1 templates print correctly on A4 sheets (tiled with alignment marks)
- [ ] Half-scale glider glides straight and level
- [ ] Full plane completes a controlled flight
- [ ] README with design rationale, calculations, build photos and flight log

## 10. Bill of materials (estimate; check local prices)

| Item | Qty |
|---|---|
| 5 mm foam board | 3–4 sheets |
| PLA or LW-PLA | ~300–500 g |
| Carbon tube or dowel (spar) | 1–2 |
| Motor, ESC, props | 1 set (+ spare props) |
| 3S LiPo + balance charger + LiPo bag | 2 batteries, 1 charger |
| 9 g servos | 4 |
| Transmitter + receiver | 1 set |
| Hot glue, packing tape, pushrod wire, M3 hardware, rubber bands | — |
