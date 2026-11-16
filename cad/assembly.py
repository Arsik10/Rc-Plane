"""
Full 3D model of the plane, built from the same numbers as the templates.

Run:  python cad/assembly.py
Writes
  docs/assembly.step    open in any CAD program
  docs/model.json       light triangle mesh for the web viewer
  docs/isometric.svg    hidden-line drawing

Aircraft axes: x aft from the firewall, y to the pilot's right, z up from the fuselage top.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cadquery as cq                                           # noqa: E402

from cad import fuselage, printed_parts, tail, wing             # noqa: E402
from cad.common import ROOT, load_design                        # noqa: E402


def _to_nose(solid):
    """Part frame (X pilot's left, Y up, Z forward) -> aircraft frame."""
    return solid.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), -90)


def _cyl(p0, p1, radius):
    a, b = cq.Vector(*p0), cq.Vector(*p1)
    return cq.Workplane("XY").add(cq.Solid.makeCylinder(radius, (b - a).Length, a, b - a))


def build(d):
    """Return {group: [solids]}; groups share a colour."""
    f, st, pr, pw, w = d["fuselage"], d["stations"], d["printed"], d["power"], d["wing"]
    H, W = f["height"], f["width"]
    zc = -H / 2
    zt = f["thrust_z"]
    groups = {"foam": [], "printed": [], "metal": [], "prop": [], "wheels": [], "wood": []}
    groups["foam"] += fuselage.solids(d) + wing.solids(d) + tail.solids(d)

    groups["printed"].append(_to_nose(printed_parts.firewall(d)).translate((0, 0, zc)))
    mm = pr["motor_mount"]
    x_face = -pr["firewall"]["plate"]
    groups["printed"].append(_to_nose(printed_parts.motor_mount(d)).translate((x_face, 0, zt)))
    x_m0 = x_face - mm["thickness"]
    groups["metal"].append(_cyl((x_m0, 0, zt), (x_m0 - pw["motor_l"], 0, zt), pw["motor_d"] / 2))
    groups["metal"].append(_cyl((x_m0 - pw["motor_l"], 0, zt), (st["prop"] - 8, 0, zt), 2.5))
    groups["prop"].append(_cyl((st["prop"] + 1, 0, zt), (st["prop"] - 1, 0, zt), d["performance"]["prop_radius"]))
    groups["printed"].append(printed_parts.wing_joiner(d).translate((st["wing_le"] + w["spar"]["x"], 0, w["spar"]["z"])))
    for x in f["band_dowels_x"]:
        groups["wood"].append(_cyl((x, -W / 2 - 14, f["band_dowel_z"]), (x, W / 2 + 14, f["band_dowel_z"]), f["band_dowel_d"] / 2))
    g = d["gear"]
    if g:
        block = printed_parts.gear_block(d).rotate((0, 0, 0), (1, 0, 0), 180).translate((g["x"], 0, -H))
        groups["printed"].append(block)
        z_ax = -H - g["axle_drop"]
        for sgn in (1, -1):
            y_top, y_ax = sgn * g["top_length"] / 2, sgn * g["track"] / 2
            groups["metal"].append(_cyl((g["x"], y_top, -H - 1.5), (g["x"], y_ax, z_ax), g["wire_d"] / 2))
            groups["metal"].append(_cyl((g["x"], y_ax, z_ax), (g["x"], y_ax + sgn * g["axle_stub"], z_ax), g["wire_d"] / 2))
            wheel = (printed_parts.wheel(d).rotate((0, 0, 0), (1, 0, 0), 90)
                     .translate((g["x"], y_ax + sgn * 6 + 6 + sgn * 8, z_ax)))
            groups["wheels"].append(wheel)
        groups["metal"].append(_cyl((g["x"], -g["top_length"] / 2, -H - 1.5), (g["x"], g["top_length"] / 2, -H - 1.5), g["wire_d"] / 2))
    return groups


def mesh_json(groups, tol=1.0):
    out = {}
    for name, solids in groups.items():
        verts, tris = [], []
        for s in solids:
            for shape in s.vals():
                v, t = shape.tessellate(tol, 0.45)
                base = len(verts) // 3
                for p in v:
                    verts += [round(p.x, 1), round(p.y, 1), round(p.z, 1)]
                for a, b, c in t:
                    tris += [a + base, b + base, c + base]
        if verts:
            out[name] = {"v": verts, "i": tris}
    return out


def main():
    d = load_design()
    groups = build(d)
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    asm = cq.Assembly(name="rc_trainer")
    colours = {"foam": (0.95, 0.95, 0.92), "printed": (1.0, 0.45, 0.1), "metal": (0.45, 0.45, 0.5),
               "prop": (0.6, 0.6, 0.6), "wheels": (0.15, 0.15, 0.15), "wood": (0.8, 0.65, 0.4)}
    everything = None
    for name, solids in groups.items():
        for k, s in enumerate(solids):
            asm.add(s, name=f"{name}_{k}", color=cq.Color(*colours[name]))
            if name != "prop":
                everything = s if everything is None else everything.add(s)
    asm.save(str(docs / "assembly.step"))
    (docs / "model.json").write_text(json.dumps(mesh_json(groups), separators=(",", ":")))
    compound = cq.Compound.makeCompound([v for v in everything.vals()])
    # the SVG exporter looks "up" along -z, so turn the model over first
    view = cq.Workplane("XY").add(compound).rotate((0, 0, 0), (1, 0, 0), 180)
    cq.exporters.export(view, str(docs / "isometric.svg"),
                        opt={"width": 900, "height": 560, "marginLeft": 20, "marginTop": 20,
                             "projectionDir": (-1.0, -1.25, -0.65), "showAxes": False, "showHidden": False,
                             "strokeWidth": 1.2})
    n = sum(len(g["i"]) // 3 for g in json.loads((docs / "model.json").read_text()).values())
    print(f"assembly: {sum(len(s) for s in groups.values())} solids, {n} triangles -> docs/")


if __name__ == "__main__":
    main()
