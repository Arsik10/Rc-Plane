"""General-arrangement drawings for the docs: three-view and wing section."""
import math

from cad import airfoil, tail, wing
from cad.drawing import Sheet


def three_view(d):
    w, t_, f, st, g, pf = d["wing"], d["tail"], d["fuselage"], d["stations"], d["gear"], d["performance"]
    h, v = t_["h"], t_["v"]
    b, c, N, Lf = w["span"], w["chord"], st["wing_le"], f["length"]
    W, H, Ht, xt = f["width"], f["height"], f["tail_height"], f["taper_start"]
    t = w["foam_t"]
    s = Sheet("three_view", "Three-view")
    T = 20.0                                           # text height, mm at full size

    # ---------------- top view (x aft to the right, y up = left wing) ------
    oy = 0.0
    s.rect(0, oy - W / 2, Lf, oy + W / 2)
    s.rect(N, oy - b / 2, N + c, oy + b / 2)
    a = w["aileron"]
    for sgn in (1, -1):
        s.poly([(N + w["hinge_x"], oy + sgn * a["y0"]), (N + c, oy + sgn * a["y0"]),
                (N + c, oy + sgn * a["y1"]), (N + w["hinge_x"], oy + sgn * a["y1"])], "cut")
    s.line((N + w["hinge_x"], oy - b / 2), (N + w["hinge_x"], oy + b / 2), "mark")
    s.rect(st["tail_le"], oy - h["span"] / 2, st["elevator_te"], oy + h["span"] / 2)
    s.line((st["tail_hinge"], oy - h["span"] / 2), (st["tail_hinge"], oy + h["span"] / 2), "bevel")
    s.rect(st["fin_le"], oy - t / 2, st["tail_hinge"] + v["rudder_root_chord"], oy + t / 2)
    pr = pf["prop_radius"]
    s.line((st["prop"], oy - pr), (st["prop"], oy + pr), "cut")
    s.rect(st["prop"] + 8, oy - 14, -3, oy + 14)
    s.line((st["cg"], oy - 60), (st["cg"], oy + 60), "fold")
    s.text((st["cg"] + 6, oy + 66), "CG", T)
    s.dim((N, oy + b / 2), (N + c, oy + b / 2), f"chord {c:.0f}", offset=14, size=T)
    s.dim((Lf + 70, oy - b / 2), (Lf + 70, oy + b / 2), f"span {b:.0f}", offset=-14, size=T)
    s.dim((st["tail_le"], oy - h["span"] / 2), (st["elevator_te"], oy - h["span"] / 2), f"{h['chord']}", offset=-14, size=T)
    s.dim((st["elevator_te"], oy - h["span"] / 2), (st["elevator_te"], oy + h["span"] / 2), f"{h['span']}", offset=-14, size=T)
    s.text((N + c + 20, oy + b / 2 - 60), f"aileron {a['chord']:.0f} x {a['length']:.0f}", T)

    # ---------------- side view ------------------------------------------
    # side and front views sit in a column to the right of the top view
    col = Lf + 260
    sx, sy = col + 120, -(b / 2) + 300
    P = lambda x, z: (sx + x, sy + z)                  # noqa: E731
    s.poly([P(0, 0), P(Lf, 0), P(Lf, -Ht), P(xt, -H), P(0, -H)])
    sec = airfoil.foam_section(c, t, w["hinge_frac"], w["flat_from"])
    s.poly([P(N + x, z) for x, z in sec.exterior.coords[:-1]])
    s.rect(sx + st["tail_le"], sy, sx + st["elevator_te"], sy + t)
    pts, hr, ht = tail.fin_outline(d)
    s.poly([P(st["fin_le"] + x, t + z) for x, z in pts])
    s.line(P(st["fin_le"] + hr[0], t + hr[1]), P(st["fin_le"] + ht[0], t + ht[1]), "bevel")
    zt = f["thrust_z"]
    s.rect(sx + st["prop"] + 8, sy + zt - 14, sx - 13, sy + zt + 14)
    s.rect(sx - 13, sy + zt - 22, sx - 3, sy + zt + 22)
    s.rect(sx - 3, sy - H, sx, sy)
    s.line(P(st["prop"], zt - pr), P(st["prop"], zt + pr), "cut")
    s.line(P(-80, zt), P(Lf + 20, zt), "mark")
    if g:
        za = -H - g["axle_drop"]
        s.line(P(g["x"], -H), P(g["x"], za), "cut")
        s.circle(P(g["x"], za), g["wheel_d"] / 2)
        ground = za - g["wheel_d"] / 2
        s.line(P(st["prop"] - 40, ground), P(g["x"] + 120, ground), "mark")
        s.text(P(g["x"] + 126, ground - 4), "ground", T * 0.8)
    # CG marker
    s.poly([P(st["cg"], -H - 6), P(st["cg"] - 12, -H - 28), P(st["cg"] + 12, -H - 28)])
    s.text(P(st["cg"] + 18, -H - 30), f"CG {d['stability']['cg_frac'] * 100:.0f}% chord", T)
    s.dim(P(0, -H - 120), P(Lf, -H - 120), f"fuselage {Lf:.0f}", offset=-14, size=T)
    s.dim(P(0, 60), P(N, 60), f"nose {N:.0f}", offset=14, size=T)
    s.dim(P(st["wing_c4"], 60), P(st["wing_c4"] + t_["arm"], 60), f"tail arm {t_['arm']:.0f}", offset=14, size=T)
    s.dim(P(st["elevator_te"] + 30, t), P(st["elevator_te"] + 30, t + v["height"]), f"{v['height']}", offset=-14, size=T)

    # ---------------- front view -----------------------------------------
    fx = col + b / 2
    fz = b / 2 - 330
    Q = lambda y, z: (fx + y, fz + z)                  # noqa: E731
    s.rect(fx - W / 2, fz - H, fx + W / 2, fz)
    dih = math.radians(w["dihedral_deg"])
    tm = w["thickness_max"]
    for sgn in (1, -1):
        tip = (sgn * b / 2 * math.cos(dih), b / 2 * math.sin(dih))
        s.poly([Q(0, 0), Q(*tip), Q(tip[0], tip[1] + tm), Q(0, tm)])
    s.rect(fx - h["span"] / 2, fz + 0, fx + h["span"] / 2, fz + t, "mark")
    s.rect(fx - t / 2, fz + t, fx + t / 2, fz + t + v["height"], "mark")
    s.circle(Q(0, zt), pr, "mark")
    s.circle(Q(0, zt), 14)
    if g:
        za = -H - g["axle_drop"]
        for sgn in (1, -1):
            s.line(Q(sgn * g["top_length"] / 2, -H), Q(sgn * g["track"] / 2, za), "cut")
            s.rect(fx + sgn * g["track"] / 2 + sgn * 4, fz + za - g["wheel_d"] / 2,
                   fx + sgn * g["track"] / 2 + sgn * 16, fz + za + g["wheel_d"] / 2)
        s.dim(Q(-g["track"] / 2, za - g["wheel_d"] / 2), Q(g["track"] / 2, za - g["wheel_d"] / 2),
              f"track {g['track']:.0f}", offset=-14, size=T)
    s.text(Q(b / 4, b / 4 * math.tan(dih) + tm + 30), f"dihedral {w['dihedral_deg']:g} deg each side", T, "middle")
    s.text((Lf / 2, b / 2 + 60), "TOP", T * 1.2, "middle")
    s.text((sx + Lf / 2, sy - H - 185), "SIDE", T * 1.2, "middle")
    s.text((fx, b / 2 + 60), "FRONT", T * 1.2, "middle")
    return s


def all_drawings(d):
    return [three_view(d), wing.section_drawing(d)]
