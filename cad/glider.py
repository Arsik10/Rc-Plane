"""
Half-scale chuck glider: same proportions, no motor, no radio.
One sheet of 5 mm foam, ten minutes to build, and it shows whether the
tail size and CG position work before any electronics are bought.
"""
from cad import tail
from cad.drawing import Sheet


def template(d, k=0.5):
    w, tl, f, st = d["wing"], d["tail"], d["fuselage"], d["stations"]
    h, v, t = tl["h"], tl["v"], w["foam_t"]
    b, c = w["span"] * k, w["chord"] * k
    s = Sheet("glider_half_scale", f"Test glider at {k:g} scale (5 mm foam, no motor)")
    # wing: flat plate with a centre crease for dihedral
    s.rect(0, 0, b, c)
    s.line((b / 2, 0), (b / 2, c), "fold")
    cg = c * (1 - d["stability"]["cg_first_flight_frac"])
    s.line((b / 2 - 25, cg), (b / 2 + 25, cg), "mark")
    s.text((b / 2 + 28, cg - 1.2), f"balance here ({d['stability']['cg_first_flight_frac'] * 100:.0f}% chord)", 3.2)
    s.text((b / 4, c / 2 - 2), "WING", 5, "middle")
    s.text((b / 2 + 3, 4), f"crease: raise each tip {b / 2 * 0.07:.0f} mm", 3.2)
    s.text((4, c - 6), "LE", 3.5)
    s.dim((0, c), (b, c), offset=7)
    s.dim((b, 0), (b, c), offset=-7)
    # profile fuselage
    Lf, H, Ht, xt = f["length"] * k, f["height"] * k, f["tail_height"] * k, f["taper_start"] * k
    y0 = -(H + 30)
    s.poly([(0, y0), (Lf, y0), (Lf, y0 - Ht), (xt, y0 - H), (0, y0 - H)])
    for x, label in ((st["wing_le"] * k, "wing LE"), (st["wing_te"] * k, "wing TE"), (st["tail_le"] * k, "stab LE")):
        s.line((x, y0), (x, y0 - 8), "mark")
        s.text((x + 1.5, y0 - 7), label, 2.8)
    s.text((xt * 0.5, y0 - H / 2 - 2), "FUSELAGE (side view) - wing and tail glue onto this top edge", 3.5, "middle")
    s.text((3, y0 - H + 3), "NOSE: tape on coins or clay until it balances", 3)
    s.dim((0, y0 - H), (xt, y0 - H), offset=-7)
    s.dim((0, y0 - H - 9), (Lf, y0 - H - 9), offset=-7)
    # tail
    y1 = y0 - H - 50
    hb, hc = h["span"] * k, h["chord"] * k
    s.rect(0, y1 - hc, hb, y1)
    s.line((hb / 2, y1 - hc), (hb / 2, y1), "mark")
    s.text((hb / 4, y1 - hc / 2 - 2), "STABILIZER", 4, "middle")
    s.dim((0, y1 - hc), (hb, y1 - hc), offset=-7)
    pts, _, _ = tail.fin_outline(d)
    cr, hv = v["root_chord"] * k, v["height"] * k
    ox = hb + 40
    s.poly([(ox, y1 - hv), (ox + cr, y1 - hv), (ox + cr, y1), (ox + cr - v["tip_chord"] * k, y1)])
    s.text((ox + cr * 0.6, y1 - hv * 0.6), "FIN", 4, "middle")
    s.dim((ox + cr, y1 - hv), (ox + cr, y1), offset=-7)
    return s
