"""
design_calc.py - turns the inputs in params.py into a complete, balanced design.

Run:  python sizing/design_calc.py

Outputs
  sizing/design.json   every derived dimension (the CAD scripts read this)
  sizing/report.md     the sizing report
  analysis/clarky.dat  the airfoil, ready to load into XFLR5
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import params as P                      # noqa: E402
from cad import airfoil                 # noqa: E402

G = 9.80665


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def air_density(elevation_m, temp_c):
    """Standard-atmosphere pressure at altitude, ideal gas at the given temperature."""
    pressure = 101325.0 * (1 - 2.25577e-5 * elevation_m) ** 5.25588
    return pressure / (287.05 * (temp_c + 273.15))


def lift_slope(aspect_ratio):
    """Lift-curve slope of a finite straight wing, per radian (Helmbold)."""
    return 2 * math.pi * aspect_ratio / (2 + math.sqrt(4 + aspect_ratio**2))


def fuselage_kf(quarter_chord_pos):
    """Gilruth/Raymer fuselage pitching-moment factor vs wing position (fraction of length)."""
    table = [(0.1, 0.003), (0.2, 0.006), (0.3, 0.011), (0.4, 0.016), (0.5, 0.024), (0.6, 0.035)]
    x = min(max(quarter_chord_pos, 0.1), 0.6)
    for (x0, k0), (x1, k1) in zip(table[:-1], table[1:]):
        if x0 <= x <= x1:
            return k0 + (k1 - k0) * (x - x0) / (x1 - x0)
    return table[-1][1]


def r(value, digits=1):
    return round(float(value), digits)


# --------------------------------------------------------------------------
# main calculation
# --------------------------------------------------------------------------
def compute(p=P):
    warn = []
    t = p.FOAM_THICKNESS
    b, c = p.WINGSPAN, p.CHORD
    half = b / 2

    # ---- 1. wing ---------------------------------------------------------
    S = b * c                                   # mm^2
    S_m2 = S / 1e6
    AR = b**2 / S
    hinge_frac = 1 - p.AILERON_CHORD_FRAC
    x_hinge = hinge_frac * c
    ail_len = p.AILERON_SPAN_FRAC * half
    ail_y1 = half - p.AILERON_TIP_MARGIN
    ail_y0 = ail_y1 - ail_len

    top = airfoil.top_skin_outline(c, t, hinge_frac, p.TOP_SKIN_FLAT_FROM)
    top_len = airfoil.polyline_length(top)
    rib = airfoil.rib_polygon(c, t, hinge_frac, p.TOP_SKIN_FLAT_FROM)
    x_spar = p.SPAR_CHORD_FRAC * c
    z_lo, z_hi = airfoil.inner_height(rib, x_spar)
    joiner_side = p.SPAR_DIAMETER + 4.0         # 2 mm printed wall each side
    if joiner_side > (z_hi - z_lo) - 0.5:
        warn.append(f"Wing joiner ({joiner_side:.1f} mm) does not fit inside the wing at the spar "
                    f"({z_hi - z_lo:.1f} mm free). Use a thinner spar or move it.")
    rib_ys = [t / 2 + i * (half - t) / (p.RIBS_PER_HALF - 1) for i in range(p.RIBS_PER_HALF)]
    thickness_max = max(z for _, z in top)
    crease_fracs = [f for f in (0.10, 0.20, 0.32) if f < p.TOP_SKIN_FLAT_FROM - 0.05] + [p.TOP_SKIN_FLAT_FROM]
    nose_len = airfoil.arc_position(top, 0.0125 * c)
    creases = [nose_len] + [airfoil.arc_position(top, f * c) for f in crease_fracs]

    wing = {
        "span": b, "chord": c, "half_span": half, "area_dm2": r(S / 1e4, 2), "aspect_ratio": r(AR, 2),
        "dihedral_deg": p.DIHEDRAL_DEG, "tip_rise": r(half * math.sin(math.radians(p.DIHEDRAL_DEG))),
        "foam_t": t, "hinge_frac": hinge_frac, "hinge_x": x_hinge,
        "flat_from": p.TOP_SKIN_FLAT_FROM, "thickness_max": r(thickness_max),
        "skin_bottom": c, "skin_top": r(top_len), "skin_total": r(c + top_len),
        "skin_creases": [r(s) for s in creases],
        "aileron": {"chord": r(p.AILERON_CHORD_FRAC * c), "y0": r(ail_y0), "y1": r(ail_y1), "length": r(ail_len)},
        "spar": {"x": r(x_spar), "z": r((z_lo + z_hi) / 2, 2), "d": p.SPAR_DIAMETER,
                 "free_height": r(z_hi - z_lo), "length_each": r(half - t)},
        "rib_y": [r(y) for y in rib_ys], "joiner_side": joiner_side, "joiner_arm": 50.0,
    }
    # aileron servo: lies on its side in the rib bay next to the inner end of the aileron
    target = ail_y0 + 0.3 * ail_len
    bay_ribs = next(((a, b2) for a, b2 in zip(rib_ys[:-1], rib_ys[1:]) if a <= target <= b2), (rib_ys[-2], rib_ys[-1]))
    servo_x, plate_t = 0.40 * c, 1.6
    ceiling = airfoil.inner_height(rib, servo_x + p.SERVO_TAB_SPAN / 2)[1]
    if plate_t + p.SERVO_BODY[1] + 0.5 > ceiling:
        warn.append(f"Aileron servo ({p.SERVO_BODY[1]} mm thick) does not fit inside the wing "
                    f"({ceiling - plate_t:.1f} mm available).")
    wing["servo"] = {"x": r(servo_x), "y": r(sum(bay_ribs) / 2), "pocket": [38.0, 34.0],
                     "plate": [48.0, 42.0, plate_t], "shaft_offset": 5.5, "ceiling": r(ceiling)}

    # ---- 2. tail ---------------------------------------------------------
    L_t = p.TAIL_ARM_CHORDS * c
    S_h = p.VH * S * c / L_t
    b_h = round(math.sqrt(p.HTAIL_ASPECT_RATIO * S_h))
    c_h = round(S_h / b_h)
    S_h = b_h * c_h
    VH_actual = S_h * L_t / (S * c)
    elev_c = round(p.ELEVATOR_CHORD_FRAC * c_h)

    S_v = p.VV * S * b / L_t
    h_v = round(math.sqrt(p.VTAIL_ASPECT_RATIO * S_v))
    c_mean = S_v / h_v
    c_vr = round(2 * c_mean / (1 + p.VTAIL_TAPER))
    c_vt = round(c_vr * p.VTAIL_TAPER)
    S_v = h_v * (c_vr + c_vt) / 2
    VV_actual = S_v * L_t / (S * b)

    tail = {
        "arm": L_t,
        "h": {"span": b_h, "chord": c_h, "area_dm2": r(S_h / 1e4, 2), "volume_coeff": r(VH_actual, 3),
              "elevator_chord": elev_c, "fixed_chord": c_h - elev_c,
              "aspect_ratio": r(b_h / c_h, 2), "area_ratio": r(S_h / S, 3)},
        "v": {"height": h_v, "root_chord": c_vr, "tip_chord": c_vt, "area_dm2": r(S_v / 1e4, 2),
              "volume_coeff": r(VV_actual, 4), "rudder_frac": p.RUDDER_CHORD_FRAC,
              "rudder_root_chord": r(p.RUDDER_CHORD_FRAC * c_vr), "rudder_tip_chord": r(p.RUDDER_CHORD_FRAC * c_vt)},
    }

    # ---- 3. foam areas that do not depend on the nose length -------------
    rho_f = p.FOAM_AREAL_DENSITY / 1e6          # g/mm^2
    wing_foam_area = 2 * half * (c + top_len) + 2 * p.RIBS_PER_HALF * rib.area
    wing_foam_x = (2 * half * c * 0.5 * c + 2 * half * top_len * 0.36 * c
                   + 2 * p.RIBS_PER_HALF * rib.area * rib.centroid.x) / wing_foam_area
    W, H, Ht = p.FUSE_WIDTH, p.FUSE_HEIGHT, p.FUSE_TAIL_HEIGHT
    h1, h2 = H - 2 * t, Ht - 2 * t

    def layout(N):
        """Everything that moves when the nose length N changes."""
        x_wle = N
        x_c4 = N + 0.25 * c
        x_cg = N + p.CG_FRAC * c
        x_tle = x_c4 + L_t - 0.25 * c_h
        x_th = x_tle + (c_h - elev_c)            # elevator hinge = end of fuselage
        Lf = x_th
        x_tp = N + c                             # taper starts at the wing TE
        Lr = Lf - x_tp
        # fuselage foam: two sides, top, bottom, formers, battery shelf
        parts = []
        parts.append((2 * x_tp * h1, x_tp / 2))
        parts.append((2 * Lr * (h1 + h2) / 2, x_tp + Lr / 3 * (h1 + 2 * h2) / (h1 + h2)))
        parts.append((W * Lf - (W - 20) * 0.8 * c, (W * Lf * Lf / 2 - (W - 20) * 0.8 * c * (N + 0.5 * c))
                      / (W * Lf - (W - 20) * 0.8 * c)))
        bottom_len = x_tp + math.hypot(Lr, H - Ht)
        parts.append((W * bottom_len, Lf / 2))
        parts.append(((W - 2 * t) * h1, x_tp))                       # former 1
        parts.append(((W - 2 * t) * (h1 + h2) / 2, x_tp + Lr / 2))   # former 2
        shelf_len = N + 0.2 * c - 20
        parts.append(((W - 2 * t) * shelf_len + 2 * 15 * shelf_len, 20 + shelf_len / 2))
        A = sum(a for a, _ in parts)
        fuse_x = sum(a * x for a, x in parts) / A

        fin_x = x_th - (1 - p.RUDDER_CHORD_FRAC) * c_vr + 0.55 * c_vr
        items = [
            ("Motor (2212)", p.MOTOR_MASS_G, -3 - 12 - p.MOTOR_LENGTH / 2),
            ("Propeller + adapter", p.PROP_MASS_G, -3 - 12 - p.MOTOR_LENGTH - 8),
            ("Printed firewall + motor mount + screws", p.PRINTED_NOSE_MASS_G, -4),
            ("ESC", p.ESC_MASS_G, 55),
            ("Receiver", p.RECEIVER_MASS_G, N + 0.75 * c),
            ("Elevator + rudder servos", 2 * p.SERVO_MASS_G, N + 0.55 * c),
            ("Aileron servos", 2 * p.SERVO_MASS_G, N + wing["servo"]["x"]),
            ("Wing foam", wing_foam_area * rho_f, N + wing_foam_x),
            ("Wing spar", p.SPAR_MASS_G_PER_M * b / 1000, N + x_spar),
            ("Printed wing joiner", p.PRINTED_JOINER_MASS_G, N + x_spar),
            ("Fuselage foam", A * rho_f, fuse_x),
            ("Stabilizer + elevator foam", S_h * rho_f, x_tle + 0.5 * c_h),
            ("Fin + rudder foam", S_v * rho_f, fin_x),
            ("Pushrods", p.PUSHRODS_MASS_G, (N + 0.55 * c + x_th) / 2),
            ("Small printed parts", p.PRINTED_SMALL_PARTS_MASS_G, N + 0.6 * c),
            ("Glue, tape, velcro, bands", p.GLUE_TAPE_MASS_G, N + 0.5 * c),
        ]
        if p.LANDING_GEAR:
            items.append(("Landing gear", p.GEAR_MASS_G, N + 0.10 * c))
        m_fixed = sum(m for _, m, _ in items)
        mom_fixed = sum(m * x for _, m, x in items)
        m_tot = m_fixed + p.BATTERY_MASS_G
        x_batt = (m_tot * x_cg - mom_fixed) / p.BATTERY_MASS_G
        bay = (20 + p.BATTERY_LENGTH / 2, N + 0.2 * c - p.BATTERY_LENGTH / 2)
        cg_range = [((mom_fixed + p.BATTERY_MASS_G * xb) / m_tot - N) / c for xb in bay]
        return dict(N=N, x_wle=x_wle, x_c4=x_c4, x_cg=x_cg, x_tle=x_tle, x_th=x_th, Lf=Lf, x_tp=x_tp,
                    bottom_len=bottom_len, shelf_len=shelf_len, items=items, m_tot=m_tot,
                    x_batt=x_batt, bay=bay, cg_range=cg_range, fuse_area=A,
                    fin_le=x_th - (1 - p.RUDDER_CHORD_FRAC) * c_vr)

    # ---- 4. balance: pick the nose length that puts the battery mid-bay --
    best = min(range(80, 401, 5), key=lambda N: abs(layout(N)["x_batt"] - sum(layout(N)["bay"]) / 2))
    lay = layout(best)
    N, Lf = lay["N"], lay["Lf"]
    if not (lay["bay"][0] <= lay["x_batt"] <= lay["bay"][1]):
        warn.append("The battery cannot reach the position needed for the design CG.")
    m_tot = lay["m_tot"]

    # ---- 5. performance --------------------------------------------------
    rho = air_density(p.FIELD_ELEVATION_M, p.AIR_TEMP_C)
    weight_n = m_tot / 1000 * G
    wing_loading = m_tot / (S / 1e4)
    v_stall = math.sqrt(2 * weight_n / (rho * S_m2 * p.CL_MAX))
    v_stall_sl = math.sqrt(2 * weight_n / (1.225 * S_m2 * p.CL_MAX))
    volts = 3.7 * p.BATTERY_CELLS
    power_w = volts * p.MOTOR_MAX_CURRENT_A
    power_loading = power_w / (m_tot / 1000)
    t_w = p.MOTOR_STATIC_THRUST_G / m_tot
    pitch_speed = p.MOTOR_KV * volts * 0.75 * p.PROP_PITCH_IN * 0.0254 / 60
    flight_min = p.BATTERY_MAH / 1000 * 0.8 / p.CRUISE_CURRENT_A * 60
    reynolds = rho * (1.3 * v_stall) * (c / 1000) / 1.85e-5

    if not p.WING_LOADING_MIN <= wing_loading <= p.WING_LOADING_MAX:
        warn.append(f"Wing loading {wing_loading:.1f} g/dm2 is outside "
                    f"{p.WING_LOADING_MIN:.0f}-{p.WING_LOADING_MAX:.0f}.")
    if v_stall > p.STALL_SPEED_MAX:
        warn.append(f"Stall speed {v_stall:.1f} m/s is above {p.STALL_SPEED_MAX} m/s.")
    if m_tot > p.AUW_TARGET_MAX_G:
        warn.append(f"Weight budget {m_tot:.0f} g is OVER the {p.AUW_TARGET_MAX_G} g target.")
    if t_w < p.THRUST_TO_WEIGHT_MIN:
        warn.append(f"Thrust-to-weight {t_w:.2f} is below {p.THRUST_TO_WEIGHT_MIN}.")
    if p.MOTOR_MAX_CURRENT_A > 0.8 * p.ESC_RATING_A:
        warn.append("Motor current is above 80% of the ESC rating.")
    if not p.POWER_LOADING_MIN <= power_loading <= p.POWER_LOADING_MAX * 1.15:
        warn.append(f"Power loading {power_loading:.0f} W/kg is outside the trainer range.")

    # ---- 6. stability (analytic estimate; confirm in XFLR5) --------------
    a_w, a_t = lift_slope(AR), lift_slope(b_h / c_h)
    downwash = 2 * a_w / (math.pi * AR)
    eta = 0.9
    tail_term = eta * VH_actual * (a_t / a_w) * (1 - downwash)
    kf = fuselage_kf(lay["x_c4"] / Lf)
    cm_fus = kf * W**2 * Lf / (c * S) * (180 / math.pi)     # per rad
    fus_shift = cm_fus / a_w
    np_frac = 0.25 + tail_term - fus_shift
    sm = np_frac - p.CG_FRAC
    sm_first = np_frac - p.CG_FIRST_FLIGHT_FRAC
    if sm <= 0:
        warn.append("UNSTABLE: the neutral point is ahead of the CG.")
    elif not p.STATIC_MARGIN_MIN <= sm <= p.STATIC_MARGIN_MAX:
        warn.append(f"Static margin {sm * 100:.1f}% is outside the "
                    f"{p.STATIC_MARGIN_MIN * 100:.0f}-{p.STATIC_MARGIN_MAX * 100:.0f}% target.")

    # ---- 7. landing gear -------------------------------------------------
    prop_r = p.PROP_DIAMETER_IN * 25.4 / 2
    thrust_z = -(H / 2) + 5                       # thrust line below the fuselage top
    gear = None
    if p.LANDING_GEAR:
        # ground must sit PROP_GROUND_CLEARANCE below the lowest point of the prop disc
        ground_drop = prop_r - thrust_z - H + p.PROP_GROUND_CLEARANCE   # below the fuselage bottom
        axle_drop = max(ground_drop, 40) - p.WHEEL_DIAMETER / 2
        run = (p.GEAR_TRACK - (W - 10)) / 2
        leg = math.hypot(run, axle_drop)
        gear = {"x": r(N + 0.10 * c), "axle_drop": r(axle_drop), "track": p.GEAR_TRACK,
                "leg_length": r(leg), "axle_stub": 25.0, "top_length": W - 10,
                "wire_length": r(W - 10 + 2 * leg + 2 * 25), "wire_d": p.GEAR_WIRE_DIAMETER,
                "wheel_d": p.WHEEL_DIAMETER}

    # ---- 8. collect ------------------------------------------------------
    fuselage = {
        "width": W, "height": H, "tail_height": Ht, "length": r(Lf), "nose_length": N,
        "length_over_span": r(Lf / b, 3),
        "taper_start": r(lay["x_tp"]), "bottom_length": r(lay["bottom_len"]),
        "hatch_end": N - 10.0, "bay_open": [r(N + 0.1 * c), r(N + 0.9 * c)], "bay_width": W - 20,
        "band_dowels_x": [N - 15.0, N + c + 15.0], "band_dowel_z": -15.0, "band_dowel_d": p.BAND_DOWEL_DIAMETER,
        "formers_x": [r(lay["x_tp"]), r((lay["x_tp"] + Lf) / 2)],
        "shelf_length": r(lay["shelf_len"]), "shelf_height": 15.0,
        "pushrod_exit_x": [r(Lf - 140), r(Lf - 105)], "thrust_z": thrust_z,
        "servo_tray_x": r(N + 0.55 * c),
    }
    stations = {
        "firewall": 0.0, "wing_le": r(N), "wing_c4": r(lay["x_c4"]), "cg": r(lay["x_cg"]),
        "cg_first_flight": r(N + p.CG_FIRST_FLIGHT_FRAC * c), "wing_te": r(N + c),
        "tail_le": r(lay["x_tle"]), "tail_hinge": r(lay["x_th"]), "fin_le": r(lay["fin_le"]),
        "elevator_te": r(lay["x_th"] + elev_c), "prop": r(-3 - 12 - p.MOTOR_LENGTH - 8),
    }
    items = [{"name": n, "mass_g": r(m), "x": r(x)} for n, m, x in lay["items"]]
    items.insert(4, {"name": f"Battery {p.BATTERY_CELLS}S {p.BATTERY_MAH} mAh",
                     "mass_g": p.BATTERY_MASS_G, "x": r(lay["x_batt"])})
    mass = {
        "items": items, "total_g": r(m_tot),
        "target_g": [p.AUW_TARGET_MIN_G, p.AUW_TARGET_MAX_G],
        "foam_areal_density": p.FOAM_AREAL_DENSITY,
        "foam_area_m2": r((wing_foam_area + lay["fuse_area"] + S_h + S_v) / 1e6, 3),
        "battery_x": r(lay["x_batt"]), "battery_bay": [r(v) for v in lay["bay"]],
        "battery_length": p.BATTERY_LENGTH,
        "cg_range_frac": [r(v, 3) for v in lay["cg_range"]],
    }
    performance = {
        "air_density": r(rho, 3), "wing_loading_g_dm2": r(wing_loading), "stall_speed_ms": r(v_stall, 2),
        "stall_speed_sea_level_ms": r(v_stall_sl, 2), "cruise_speed_ms": r(1.6 * v_stall),
        "reynolds_at_1p3_stall": int(round(reynolds, -3)),
        "power_w": r(power_w), "power_loading_w_kg": r(power_loading), "thrust_to_weight": r(t_w, 2),
        "pitch_speed_ms": r(pitch_speed), "pitch_speed_over_stall": r(pitch_speed / v_stall, 2),
        "flight_time_min": r(flight_min), "prop": f"{p.PROP_DIAMETER_IN:g}x{p.PROP_PITCH_IN:g}",
        "prop_radius": r(prop_r),
    }
    stability = {
        "cg_frac": p.CG_FRAC, "cg_first_flight_frac": p.CG_FIRST_FLIGHT_FRAC,
        "wing_lift_slope": r(a_w, 3), "tail_lift_slope": r(a_t, 3), "downwash_gradient": r(downwash, 3),
        "tail_efficiency": eta, "tail_contribution": r(tail_term, 4), "fuselage_shift": r(fus_shift, 4),
        "neutral_point_frac": r(np_frac, 4), "neutral_point_x": r(N + np_frac * c),
        "static_margin": r(sm, 4), "static_margin_first_flight": r(sm_first, 4),
    }
    sv = p.SERVO_BODY
    printed = {
        "firewall": {"width": W, "height": H, "plate": 3.0, "lip_depth": 12.0, "lip_wall": 1.6,
                     "inner_w": W - 2 * t, "inner_h": H - 2 * t, "bolt_square": 34.0,
                     "motor_axis_up": 5.0},
        "motor_mount": {"size": 44.0, "thickness": 10.0, "bolt_square": 34.0,
                        "motor_holes": list(p.MOTOR_HOLE_SPACING),
                        "right_deg": p.RIGHT_THRUST_DEG, "down_deg": p.DOWN_THRUST_DEG},
        "joiner": {"side": joiner_side, "arm": wing["joiner_arm"], "bore": p.SPAR_DIAMETER + 0.3,
                   "dihedral_deg": p.DIHEDRAL_DEG},
        "servo": {"body": list(sv), "tab_span": p.SERVO_TAB_SPAN, "hole_spacing": p.SERVO_HOLE_SPACING,
                  "tab_height": p.SERVO_TAB_HEIGHT},
        "servo_tray": {"width": W - 2 * t - 0.6, "length": 44.0, "thickness": 2.4},
        "gear_block": {"length": W - 2 * t - 0.6, "width": 22.0, "height": 9.0},
        "m3_clearance": p.M3_CLEARANCE, "m3_head": p.M3_HEAD_DIAMETER,
        "bed": list(p.PRINTER_BED), "min_wall": p.MIN_WALL,
    }
    throws = {"aileron_mm": 10, "elevator_mm": 8, "rudder_mm": 15}
    return {"wing": wing, "tail": tail, "fuselage": fuselage, "stations": stations, "mass": mass,
            "performance": performance, "stability": stability, "gear": gear, "printed": printed,
            "throws": throws, "warnings": warn,
            "site": {"elevation_m": p.FIELD_ELEVATION_M, "temp_c": p.AIR_TEMP_C},
            "power": {"kv": p.MOTOR_KV, "cells": p.BATTERY_CELLS, "mah": p.BATTERY_MAH,
                      "thrust_g": p.MOTOR_STATIC_THRUST_G, "current_a": p.MOTOR_MAX_CURRENT_A,
                      "esc_a": p.ESC_RATING_A, "motor_d": p.MOTOR_DIAMETER, "motor_l": p.MOTOR_LENGTH}}


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------
def report(d):
    w, tl, f, st, m, pf, sb = (d["wing"], d["tail"], d["fuselage"], d["stations"], d["mass"],
                               d["performance"], d["stability"])
    c = w["chord"]
    ok = lambda cond: "OK" if cond else "CHECK"   # noqa: E731
    L = []
    L.append("# Sizing report\n")
    L.append("Generated by `sizing/design_calc.py` from `params.py`. Do not edit by hand.\n")
    if d["warnings"]:
        L.append("## Warnings\n")
        L += [f"- **{x}**" for x in d["warnings"]]
        L.append("")
    else:
        L.append("All checks pass.\n")
    L.append("## 1. Wing\n")
    L.append("| Quantity | Formula | Value |\n|---|---|---|")
    L.append(f"| Span b | input | {w['span']:.0f} mm |")
    L.append(f"| Chord c | input | {c:.0f} mm |")
    L.append(f"| Area S | b x c | {w['area_dm2']} dm2 |")
    L.append(f"| Aspect ratio | b2 / S | {w['aspect_ratio']} |")
    L.append(f"| Dihedral | input | {w['dihedral_deg']} deg per side (tip rises {w['tip_rise']} mm) |")
    L.append(f"| Section | Clark Y, flat bottom, folded foam | {w['thickness_max']} mm thick "
             f"({w['thickness_max'] / c * 100:.1f}%) |")
    L.append(f"| Aileron | {w['aileron']['chord'] / c * 100:.0f}% chord | {w['aileron']['chord']:.0f} x "
             f"{w['aileron']['length']:.0f} mm, from {w['aileron']['y0']:.0f} to {w['aileron']['y1']:.0f} mm "
             f"from the root |")
    L.append(f"| Spar | {w['spar']['x'] / c * 100:.0f}% chord | {w['spar']['d']:.0f} mm, two pieces of "
             f"{w['spar']['length_each']:.0f} mm |")
    L.append("\n## 2. Weight and wing loading\n")
    L.append("| Item | Mass (g) | Position from firewall (mm) |\n|---|---:|---:|")
    for it in m["items"]:
        L.append(f"| {it['name']} | {it['mass_g']:.0f} | {it['x']:.0f} |")
    L.append(f"| **All-up weight** | **{m['total_g']:.0f}** | CG at {st['cg']:.0f} |")
    L.append(f"\nTarget {m['target_g'][0]}-{m['target_g'][1]} g: "
             f"**{ok(m['total_g'] <= m['target_g'][1])}**"
             + (" (lighter than the window, which only helps)" if m["total_g"] < m["target_g"][0] else "")
             + f". Foam used: {m['foam_area_m2']} m2 at {m['foam_areal_density']:.0f} g/m2.\n")
    L.append("| Quantity | Formula | Value | Target |\n|---|---|---|---|")
    L.append(f"| Wing loading | W / S | {pf['wing_loading_g_dm2']} g/dm2 | 30-45 |")
    L.append(f"| Air density | ISA pressure at {d['site']['elevation_m']} m, {d['site']['temp_c']} C | "
             f"{pf['air_density']} kg/m3 | |")
    L.append(f"| Stall speed | sqrt(2W / (rho S CLmax)) | {pf['stall_speed_ms']} m/s "
             f"({pf['stall_speed_ms'] * 3.6:.0f} km/h) | < 9 |")
    L.append(f"| Stall speed at sea level | same, rho = 1.225 | {pf['stall_speed_sea_level_ms']} m/s | |")
    L.append(f"| Comfortable cruise | about 1.6 x stall | {pf['cruise_speed_ms']} m/s | |")
    L.append(f"| Reynolds number near stall | rho V c / mu | {pf['reynolds_at_1p3_stall']:,} | |")
    L.append("\n## 3. Fuselage and tail\n")
    L.append("| Quantity | Formula | Value |\n|---|---|---|")
    L.append(f"| Tail arm L_t | {tl['arm'] / c:.2f} x c | {tl['arm']:.0f} mm |")
    L.append(f"| Horizontal tail area | V_h S c / L_t | {tl['h']['area_dm2']} dm2 "
             f"({tl['h']['area_ratio'] * 100:.0f}% of wing), V_h = {tl['h']['volume_coeff']} |")
    L.append(f"| Horizontal tail | AR {tl['h']['aspect_ratio']} | {tl['h']['span']} x {tl['h']['chord']} mm, "
             f"elevator {tl['h']['elevator_chord']} mm |")
    L.append(f"| Vertical tail area | V_v S b / L_t | {tl['v']['area_dm2']} dm2, V_v = {tl['v']['volume_coeff']} |")
    L.append(f"| Fin | taper {tl['v']['tip_chord'] / tl['v']['root_chord']:.2f} | height {tl['v']['height']} mm, "
             f"root {tl['v']['root_chord']} mm, tip {tl['v']['tip_chord']} mm, rudder "
             f"{tl['v']['rudder_frac'] * 100:.0f}% of chord |")
    L.append(f"| Nose length (firewall to wing LE) | solved from the balance | {f['nose_length']:.0f} mm |")
    L.append(f"| Fuselage length (firewall to elevator hinge) | nose + c/4 + L_t + tail | {f['length']:.0f} mm "
             f"= {f['length_over_span'] * 100:.0f}% of span |")
    L.append(f"| Fuselage section | input | {f['width']:.0f} x {f['height']:.0f} mm, {f['tail_height']:.0f} mm "
             f"high at the tail |")
    if not 0.70 <= f["length_over_span"] <= 0.75:
        L.append(f"\nThe rule of thumb says 70-75% of span. This fuselage is {f['length_over_span'] * 100:.0f}% "
                 "because the nose length is not guessed: it is the length at which the battery sits in the "
                 "middle of its bay with the CG on target, so the battery can still be moved either way.")
    L.append("\n## 4. Balance\n")
    L.append(f"- Design CG: **{sb['cg_frac'] * 100:.0f}% chord = {sb['cg_frac'] * c:.0f} mm behind the wing "
             f"leading edge** ({st['cg']:.0f} mm from the firewall).")
    L.append(f"- First flight CG: {sb['cg_first_flight_frac'] * 100:.0f}% chord = "
             f"{sb['cg_first_flight_frac'] * c:.0f} mm behind the leading edge.")
    L.append(f"- Battery centre for the design CG: {m['battery_x']:.0f} mm from the firewall "
             f"(the bay lets it sit anywhere from {m['battery_bay'][0]:.0f} to {m['battery_bay'][1]:.0f} mm).")
    L.append(f"- Sliding the battery end to end moves the CG from {m['cg_range_frac'][0] * 100:.0f}% to "
             f"{m['cg_range_frac'][1] * 100:.0f}% chord.")
    L.append("\n## 5. Stability estimate\n")
    L.append("Hand calculation; confirm in XFLR5 (see `analysis/xflr5_notes.md`).\n")
    L.append("| Quantity | Formula | Value |\n|---|---|---|")
    L.append(f"| Wing lift slope a_w | 2 pi AR / (2 + sqrt(4 + AR2)) | {sb['wing_lift_slope']} /rad |")
    L.append(f"| Tail lift slope a_t | same, tail AR | {sb['tail_lift_slope']} /rad |")
    L.append(f"| Downwash gradient | 2 a_w / (pi AR) | {sb['downwash_gradient']} |")
    L.append(f"| Tail contribution | eta V_h (a_t/a_w)(1 - de/da), eta = {sb['tail_efficiency']} | "
             f"+{sb['tail_contribution'] * 100:.1f}% c |")
    L.append(f"| Fuselage contribution | K_f w2 L / (c S a_w) | -{sb['fuselage_shift'] * 100:.1f}% c |")
    L.append(f"| Neutral point | 0.25 + tail - fuselage | {sb['neutral_point_frac'] * 100:.1f}% c "
             f"({sb['neutral_point_frac'] * c:.0f} mm behind the LE) |")
    L.append(f"| **Static margin at design CG** | NP - CG | **{sb['static_margin'] * 100:.1f}%** (target 10-15%) |")
    L.append(f"| Static margin at first-flight CG | | {sb['static_margin_first_flight'] * 100:.1f}% |")
    L.append("\n## 6. Power\n")
    L.append("| Quantity | Formula | Value | Target |\n|---|---|---|---|")
    L.append(f"| Electrical power | V x I = {3.7 * d['power']['cells']:.1f} V x {d['power']['current_a']} A | "
             f"{pf['power_w']:.0f} W | |")
    L.append(f"| Power loading | P / m | {pf['power_loading_w_kg']:.0f} W/kg | 150-200 |")
    L.append(f"| Thrust-to-weight | static thrust / weight | {pf['thrust_to_weight']} | >= 0.8 |")
    L.append(f"| Pitch speed | 0.75 KV V x pitch | {pf['pitch_speed_ms']} m/s = "
             f"{pf['pitch_speed_over_stall']} x stall | >= 2 x stall |")
    L.append(f"| Flight time | 80% of capacity / average current | about {pf['flight_time_min']:.0f} min | |")
    if d["gear"]:
        g = d["gear"]
        L.append("\n## 7. Landing gear\n")
        L.append(f"- Main gear block centred {g['x']:.0f} mm from the firewall.")
        L.append(f"- Axle {g['axle_drop']:.0f} mm below the fuselage bottom gives the "
                 f"{pf['prop']} propeller {P.PROP_GROUND_CLEARANCE:.0f} mm of ground clearance.")
        L.append(f"- Wire: {g['wire_d']:.0f} mm, total length {g['wire_length']:.0f} mm "
                 f"({g['top_length']:.0f} flat + 2 x {g['leg_length']:.0f} legs + 2 x {g['axle_stub']:.0f} axles).")
    L.append("\n## 8. Control throws to start with\n")
    L.append(f"Measured at the trailing edge: aileron +/-{d['throws']['aileron_mm']} mm, elevator "
             f"+/-{d['throws']['elevator_mm']} mm, rudder +/-{d['throws']['rudder_mm']} mm.\n")
    return "\n".join(L)


def main():
    d = compute()
    (ROOT / "sizing" / "design.json").write_text(json.dumps(d, indent=1))
    text = report(d)
    (ROOT / "sizing" / "report.md").write_text(text)
    (ROOT / "analysis").mkdir(exist_ok=True)
    (ROOT / "analysis" / "clarky.dat").write_text(airfoil.selig_dat())
    print(text)
    return d


if __name__ == "__main__":
    main()
