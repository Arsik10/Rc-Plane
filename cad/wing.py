"""
Wing: folded foam-board Clark Y with a flat bottom.

Each half is ONE sheet: bottom plate, a fold at the leading edge, then the top
skin, which wraps over the ribs and lands on the bottom plate at the hinge
line. Behind the hinge line the bottom plate alone forms the trailing edge
and the aileron.
"""
from shapely.geometry import box

from cad import airfoil
from cad.drawing import Sheet


def _rib(d):
    w = d["wing"]
    return airfoil.rib_polygon(w["chord"], w["foam_t"], w["hinge_frac"], w["flat_from"])


def skin_template(d):
    """Flat pattern of one wing half, seen from the inside (the side you glue on)."""
    w = d["wing"]
    c, half, top = w["chord"], w["half_span"], w["skin_top"]
    ail, sp, sv = w["aileron"], w["spar"], w["servo"]
    s = Sheet("wing_half", "Wing half - folded skin (cut 2: one as drawn, one mirrored)")
    total = c + top
    s.rect(0, 0, half, total)
    # v = 0 is the trailing edge; v = c is the leading-edge fold
    le = c
    s.line((0, le), (half, le), "fold")
    s.text((half / 2, le + 1.5), "LEADING EDGE - fold line 1", 4, "middle")
    for i, pos in enumerate(w["skin_creases"]):
        s.line((0, le + pos), (half, le + pos), "fold")
        label = "fold line 2 (nose)" if i == 0 else ("crease: top skin goes flat from here" if i == len(w["skin_creases"]) - 1
                                                     else "crease (score lightly)")
        s.text((6, le + pos + 1.5), label, 3.2)
    s.text((half / 2, total - 9), "TOP SKIN - this edge is glued down along the hinge line", 4, "middle")
    s.text((half / 2, le - 40), "BOTTOM PLATE (inside face)", 5, "middle")
    # hinge line / landing line of the top skin
    v_h = c - w["hinge_x"]
    s.line((0, v_h), (ail["y0"], v_h), "mark")
    s.line((ail["y1"], v_h), (half, v_h), "mark")
    s.line((ail["y0"], v_h), (ail["y1"], v_h), "bevel")
    s.line((ail["y0"], 0), (ail["y0"], v_h), "cut")
    s.line((ail["y1"], 0), (ail["y1"], v_h), "cut")
    s.text(((ail["y0"] + ail["y1"]) / 2, v_h / 2 - 2), f"AILERON {ail['chord']:.0f} x {ail['length']:.0f}", 5, "middle")
    s.text((8, v_h + 1.5), "hinge line: top skin lands here", 3.2)
    s.text((half / 2 - 60, 3), "TRAILING EDGE", 4, "middle")
    # spar and ribs
    v_s = c - sp["x"]
    s.line((0, v_s), (half, v_s), "mark")
    s.text((half - 4, v_s + 1.5), f"spar centre line ({sp['d']:.0f} mm)", 3.2, "end")
    rib = _rib(d)
    rx0, _, rx1, _ = rib.bounds
    for i, y in enumerate(w["rib_y"]):
        s.rect(y - w["foam_t"] / 2, c - rx1, y + w["foam_t"] / 2, c - rx0, "mark")
        s.text((y + 4, c - rx1 + 3), f"rib {i + 1}" + (" (root)" if i == 0 else ""), 3.2)
    # servo pocket and lead hole
    px, py = sv["pocket"]
    s.rect(sv["y"] - py / 2, c - sv["x"] - px / 2, sv["y"] + py / 2, c - sv["x"] + px / 2, "cut")
    s.text((sv["y"], c - sv["x"] - px / 2 - 5), "servo pocket", 3.2, "middle")
    s.circle((22, c - 0.42 * c), 6, "cut")
    s.text((30, c - 0.42 * c - 1), "servo lead exit", 3.2)
    s.text((3, total / 2), "ROOT", 5, "start", 90)
    s.text((half - 3, total / 2 + 30), "TIP", 5, "start", 90)
    s.dim((0, 0), (half, 0), offset=-8)
    s.dim((half, 0), (half, c), offset=-8)
    s.dim((half, c), (half, total), offset=-8)
    return s


def rib_template(d):
    w = d["wing"]
    c, sp = w["chord"], w["spar"]
    rib = _rib(d)
    s = Sheet("wing_ribs", f"Wing ribs - cut {2 * (len(w['rib_y']) - 1)} standard + 2 root")
    lift = lambda poly, dz: [(x, z + dz) for x, z in poly.exterior.coords[:-1]]   # noqa: E731
    # standard rib
    s.poly(lift(rib, 0))
    s.circle((sp["x"], sp["z"]), (sp["d"] + 0.4) / 2)
    zlo, zhi = airfoil.inner_height(rib, 0.42 * c)
    s.circle((0.42 * c, (zlo + zhi) / 2), 4)
    s.text((0.62 * c, w["foam_t"] + 16), "STANDARD RIB", 3.5)
    s.text((sp["x"], w["foam_t"] - 5), "spar", 3, "middle")
    s.text((0.42 * c, w["foam_t"] - 5), "servo lead", 3, "middle")
    # root rib: full-height slot for the printed joiner
    dz = -34
    slot = box(sp["x"] - w["joiner_side"] / 2 - 0.3, -10, sp["x"] + w["joiner_side"] / 2 + 0.3, 100)
    root = rib.difference(slot)
    for g in getattr(root, "geoms", [root]):
        s.poly(lift(g, dz))
    s.circle((0.42 * c, (zlo + zhi) / 2 + dz), 4)
    s.text((0.62 * c, w["foam_t"] + 16 + dz), "ROOT RIB: two pieces,", 3.5)
    s.text((0.62 * c, w["foam_t"] + 11 + dz), "the joiner sits in the gap", 3.5)
    # true Clark Y for reference
    dz = -80
    prof = airfoil.true_profile(c)
    s.poly([(x, z + dz) for x, z in prof], "mark")
    s.line((0, dz), (c, dz), "mark")
    s.text((c / 2, dz + 8), f"reference: true Clark Y, chord {c:.0f} mm (do not cut)", 3.5, "middle")
    s.dim((0, dz - 4), (c, dz - 4), offset=-4)
    return s


def section_drawing(d):
    """Cross-section of the built wing, for the build guide."""
    w = d["wing"]
    c, t, sp = w["chord"], w["foam_t"], w["spar"]
    s = Sheet("wing_section", "Wing section as built")
    sec = airfoil.foam_section(c, t, w["hinge_frac"], w["flat_from"])
    s.poly(list(sec.exterior.coords[:-1]))
    rib = _rib(d)
    s.poly(list(rib.exterior.coords[:-1]), "mark")
    s.line((0, t), (w["hinge_x"], t), "mark")
    s.circle((sp["x"], sp["z"]), sp["d"] / 2)
    s.poly([(x, z) for x, z in airfoil.true_profile(c)], "mark")
    s.text((sp["x"], sp["z"] + 14), "spar", 5, "middle")
    s.text((0.45 * c, 9), "rib", 5, "middle")
    s.text((w["hinge_x"] + 4, t + 4), "hinge", 5)
    s.text((c - 2, -8), "aileron / trailing edge plate", 5, "end")
    s.text((4, -8), "fold", 5)
    s.dim((0, -12), (c, -12), offset=-6, size=6)
    return s


def templates(d):
    return [skin_template(d), rib_template(d)]


# ---- 3D ------------------------------------------------------------------
def solids(d):
    """Two wing halves in aircraft coordinates (x aft from firewall, y right, z up)."""
    import cadquery as cq
    w = d["wing"]
    c, t, xh = w["chord"], w["foam_t"], w["hinge_x"]
    top = airfoil.top_skin_outline(c, t, w["hinge_frac"], w["flat_from"], n=24)
    curve = [(float(x), float(z)) for x, z in top[1:-1]]
    left = (cq.Workplane("XZ").moveTo(0, 0).lineTo(*curve[0]).spline(curve[1:], includeCurrent=True)
            .lineTo(xh, 2 * t).lineTo(xh, t).lineTo(c, t).lineTo(c, 0).close()
            .extrude(w["half_span"]))                                         # extrudes toward -y
    left = left.rotate((0, 0, 0), (1, 0, 0), -w["dihedral_deg"])
    right = left.mirror("XZ")
    move = (d["stations"]["wing_le"], 0, 0)
    return [left.translate(move), right.translate(move)]
