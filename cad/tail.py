"""Tail surfaces: flat 5 mm foam plates sized by the calculator."""
import math

from cad.drawing import Sheet

RUDDER_CLEAR = 3.0          # gap between the rudder and the elevator at the hinge
RUDDER_SLANT_DEG = 25.0     # the rudder bottom slopes up so the elevator can rise


def fin_outline(d):
    """Fin + rudder outline in local coords: x aft from the fin root LE, z up from the stabilizer top."""
    v, h, t = d["tail"]["v"], d["tail"]["h"], d["wing"]["foam_t"]
    cr, ct, hv, fr = v["root_chord"], v["tip_chord"], v["height"], v["rudder_frac"]
    hinge_root, hinge_tip = cr * (1 - fr), cr - fr * ct
    step = d["stations"]["tail_le"] - d["stations"]["fin_le"]      # fin starts ahead of the stabilizer
    rise = RUDDER_CLEAR + fr * cr * math.tan(math.radians(RUDDER_SLANT_DEG))
    pts = []
    if step > 1:
        pts += [(0, -t), (step, -t), (step, 0)]
    else:
        pts += [(0, 0)]
    pts += [(hinge_root, 0), (hinge_root, RUDDER_CLEAR), (cr, rise), (cr, hv), (cr - ct, hv)]
    return pts, (hinge_root, RUDDER_CLEAR), (hinge_tip, hv)


def template(d):
    h, v, thr = d["tail"]["h"], d["tail"]["v"], d["throws"]
    b, c, ce = h["span"], h["chord"], h["elevator_chord"]
    s = Sheet("tail", "Tail - stabilizer + elevator, fin + rudder")
    # stabilizer, leading edge at the top of the drawing
    s.rect(0, 0, b, c)
    s.line((0, ce), (b, ce), "bevel")
    s.line((b / 2, ce), (b / 2, c), "mark")
    s.text((b / 2 + 3, c - 8), "centre line: fin stands here", 3.2)
    s.text((b / 4, ce + (c - ce) / 2 - 2), "STABILIZER", 5, "middle")
    s.text((b / 4, ce / 2 - 2), f"ELEVATOR (throw +/-{thr['elevator_mm']} mm)", 4.5, "middle")
    s.rect(b / 2 - 36, ce - 14, b / 2 - 24, ce - 2, "mark")
    s.text((b / 2 - 40, ce - 10), "horn, underside", 3, "end")
    s.text((4, c - 6), "LE", 3.5)
    s.dim((0, c), (b, c), offset=7)
    s.dim((b, 0), (b, ce), offset=-7)
    s.dim((b, ce), (b, c), offset=-7)
    # fin
    pts, hr, ht = fin_outline(d)
    ox, oy = 20.0, -(v["height"] + 30)
    s.poly([(x + ox, z + oy) for x, z in pts])
    s.line((hr[0] + ox, hr[1] + oy), (ht[0] + ox, ht[1] + oy), "bevel")
    s.text((ox + v["root_chord"] * 0.42, oy + v["height"] * 0.3), "FIN", 5, "middle")
    s.text((ox + v["root_chord"] - 4, oy + v["height"] * 0.55), "RUDDER", 4, "end", 90)
    s.rect(hr[0] + ox + 3, oy + 22, hr[0] + ox + 15, oy + 34, "mark")
    s.text((ox + v["root_chord"] + 26, oy + 26), "horn, right side", 3)
    s.text((ox + v["root_chord"] + 26, oy + 12), f"rudder throw +/-{thr['rudder_mm']} mm", 3)
    s.dim((ox + v["root_chord"], oy), (ox + v["root_chord"], oy + v["height"]), offset=-10)
    s.dim((ox + v["root_chord"] - v["tip_chord"], oy + v["height"]), (ox + v["root_chord"], oy + v["height"]), offset=7)
    s.dim((ox, oy - 6), (ox + v["root_chord"], oy - 6), offset=-6)
    return s


def templates(d):
    return [template(d)]


def solids(d):
    import cadquery as cq
    h, st, t = d["tail"]["h"], d["stations"], d["wing"]["foam_t"]
    stab = (cq.Workplane("XY").box(h["chord"], h["span"], t, centered=(False, True, False))
            .translate((st["tail_le"], 0, 0)))
    pts, _, _ = fin_outline(d)
    fin = (cq.Workplane("XZ").polyline(pts).close().extrude(t)
           .translate((st["fin_le"], t / 2, t)))
    return [stab, fin]
