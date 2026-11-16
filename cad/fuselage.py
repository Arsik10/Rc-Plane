"""
Fuselage: a foam-board box.

Shell   one piece: side - top - side, folded down along two "B-folds"
        (5 mm channel of foam removed, the paper skin stays as the hinge)
Bottom  one strip, glued under the sides, creased where the tail taper starts
Hatch   loose lid over the battery bay
"""
from cad.drawing import Sheet


def shell_template(d):
    f, st, w = d["fuselage"], d["stations"], d["wing"]
    t = w["foam_t"]
    W, H, Ht, Lf = f["width"], f["height"], f["tail_height"], f["length"]
    h1, h2 = H - 2 * t, Ht - 2 * t
    xt, xh = f["taper_start"], f["hatch_end"]
    a = W / 2 + t                      # inner edge of the side panel
    s = Sheet("fuselage_shell", "Fuselage shell - sides + top, one piece")
    s.poly([(0, a), (0, a + h1), (xt, a + h1), (Lf, a + h2), (Lf, -(a + h2)), (xt, -(a + h1)),
            (0, -(a + h1)), (0, -a), (xh, -a), (xh, a)])
    for sign in (1, -1):
        s.line((xh, sign * W / 2), (Lf, sign * W / 2), "fold")
        s.line((xh, sign * a), (Lf, sign * a), "fold")
        s.text((Lf - 60, sign * (W / 2 + 1.2) - (0 if sign > 0 else 2.5)), "B-fold: remove the foam between the two lines", 2.6, "end")
        # wing band dowels, pushrod exits, formers, CG mark
        for x in f["band_dowels_x"]:
            s.circle((x, sign * (W / 2 - f["band_dowel_z"])), f["band_dowel_d"] / 2)
        e0, e1 = f["pushrod_exit_x"]
        v = sign * (a + 9)
        s.rect(e0, v - 2, e1, v + 2)
        for x in f["formers_x"]:
            hh = h1 if x <= xt else h1 + (h2 - h1) * (x - xt) / (Lf - xt)
            s.line((x, sign * a), (x, sign * (a + hh)), "mark")
        s.line((st["cg"], sign * (a + 2)), (st["cg"], sign * (a + 22)), "mark")
        s.text((st["cg"] + 2, sign * (a + 14)), "CG", 4)
        vr = a + h1 - f["shelf_height"]           # top edge of the shelf rail
        s.line((20, sign * vr), (f["shelf_length"] + 20, sign * vr), "mark")
        s.text((xt / 2, sign * (a + h1 / 2 + 8)), "SIDE", 6, "middle")
        s.text((30, sign * (vr - 4) - (0 if sign > 0 else 3)), "battery shelf rail (top edge)", 2.8)
    s.text((e0 - 3, a + 7.5), "pushrod exit slots", 3, "end")
    s.text((f["band_dowels_x"][0] + 5, W / 2 - f["band_dowel_z"] - 1), "wing band dowel", 3)
    # wing bay opening and wing position
    b0, b1 = f["bay_open"]
    s.rect(b0, -f["bay_width"] / 2, b1, f["bay_width"] / 2)
    s.text(((b0 + b1) / 2, -2), "WING BAY - cut out", 4.5, "middle")
    for x, label in ((st["wing_le"], "wing LE"), (st["wing_te"], "wing TE"), (st["tail_le"], "stabilizer LE")):
        s.line((x, -W / 2), (x, W / 2), "mark")
        s.text((x + 2, W / 2 - 6), label, 3)
    s.text(((st["wing_te"] + st["tail_le"]) / 2, -2), "TOP", 6, "middle")
    s.text((xh / 2, 0), "hatch goes here", 4, "middle")
    s.text((4, a + h1 - 8), "NOSE (firewall)", 4)
    s.text((Lf - 4, a + h2 - 7), "TAIL", 4, "end")
    s.dim((0, -(a + h1)), (xt, -(a + h1)), offset=-7)
    s.dim((0, -(a + h1) - 9), (Lf, -(a + h1) - 9), offset=-7)
    s.dim((0, a), (0, a + h1), offset=7)
    s.dim((Lf, a + h2), (Lf, a), offset=7)
    s.dim((xh, -W / 2), (xh, W / 2), offset=7)
    return s


def bottom_template(d):
    f, w, g = d["fuselage"], d["wing"], d["gear"]
    t = w["foam_t"]
    W, xt, L = f["width"], f["taper_start"], f["bottom_length"]
    s = Sheet("fuselage_bottom_hatch", "Fuselage bottom + battery hatch")
    s.rect(0, 0, L, W)
    s.line((xt, 0), (xt, W), "fold")
    s.text((xt + 3, W / 2), "crease: tail taper starts", 3.2)
    s.text((xt / 2, W / 2 + 8), "BOTTOM (outside face)", 5, "middle")
    s.text((4, 5), "NOSE", 4)
    if g:
        gb = d["printed"]["gear_block"]
        s.rect(g["x"] - gb["width"] / 2, (W - gb["length"]) / 2, g["x"] + gb["width"] / 2, (W + gb["length"]) / 2, "mark")
        s.text((g["x"], W / 2 - 1.5), "gear block", 3, "middle")
    s.dim((0, 0), (L, 0), offset=-7)
    s.dim((L, 0), (L, W), offset=-7)
    # hatch
    y0 = W + 30
    hl = f["hatch_end"] - 1.0
    s.rect(0, y0, hl, y0 + W)
    s.text((hl / 2, y0 + W / 2 - 2), "BATTERY HATCH", 5, "middle")
    s.dim((0, y0 + W), (hl, y0 + W), offset=7)
    return s


def small_parts_template(d):
    f, w = d["fuselage"], d["wing"]
    t = w["foam_t"]
    W, H, Ht = f["width"], f["height"], f["tail_height"]
    iw, h1, h2 = W - 2 * t, H - 2 * t, Ht - 2 * t
    s = Sheet("small_parts", "Formers, battery shelf, wing locators")
    x = 0.0
    # former 1
    s.rect(x, 0, x + iw, h1)
    s.rect(x + 12, 14, x + iw - 12, h1 - 10)
    s.text((x + iw / 2, h1 + 3), "FORMER 1 (at wing TE)", 3.2, "middle")
    s.dim((x, 0), (x + iw, 0), offset=-6)
    s.dim((x, 0), (x, h1), offset=6)
    # former 2
    x += iw + 30
    hm = (h1 + h2) / 2
    s.rect(x, 0, x + iw, hm)
    s.rect(x + 12, 12, x + iw - 12, hm - 8)
    s.text((x + iw / 2, hm + 3), "FORMER 2 (mid tail)", 3.2, "middle")
    s.dim((x, 0), (x, hm), offset=6)
    # wing locators
    x += iw + 30
    lw = f["bay_width"] - 1
    for k in range(2):
        s.rect(x, k * 30, x + lw, k * 30 + 20)
        s.text((x + lw / 2, k * 30 + 8), "wing locator", 3, "middle")
    s.dim((x, 0), (x + lw, 0), offset=-6)
    # shelf + rails
    y0 = -(iw + 30)
    sl = f["shelf_length"]
    s.rect(0, y0, sl, y0 + iw)
    s.text((sl / 2, y0 + iw / 2 - 2), "BATTERY SHELF", 5, "middle")
    s.dim((0, y0), (sl, y0), offset=-6)
    s.dim((sl, y0), (sl, y0 + iw), offset=-6)
    for k in range(2):
        yy = y0 - 30 - k * 22
        s.rect(0, yy, sl, yy + 15)
        s.text((sl / 2, yy + 5), "shelf rail 15 mm", 3.2, "middle")
    return s


def templates(d):
    return [shell_template(d), bottom_template(d), small_parts_template(d)]


def solids(d):
    import cadquery as cq
    f = d["fuselage"]
    W, H, Ht, Lf, xt = f["width"], f["height"], f["tail_height"], f["length"], f["taper_start"]
    body = (cq.Workplane("XZ").polyline([(0, 0), (Lf, 0), (Lf, -Ht), (xt, -H), (0, -H)]).close()
            .extrude(W).translate((0, W / 2, 0)))
    return [body]
