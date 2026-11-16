"""
3D-printed parts (CadQuery). Every dimension comes from sizing/design.json.

Run:  python cad/printed_parts.py      -> writes stl/*.stl and stl/PRINT_LIST.md

Local axes are given in each function. All parts print without supports in
the orientation they are exported in (flat face on the bed).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cadquery as cq                                   # noqa: E402

from cad.common import ROOT, load_design                # noqa: E402

PLA_DENSITY = 1.24e-3      # g/mm^3
PILOT = 1.6                # pilot hole for the small servo screws


def firewall(d):
    """Nose cap, drawn as seen from the front. X = pilot's left, Y up, Z forward.
    Plate at z 0..3, glue lip goes back into the foam box."""
    f = d["printed"]["firewall"]
    cl = d["printed"]["m3_clearance"]
    lip, wall = f["lip_depth"], f["lip_wall"]
    iw, ih = f["inner_w"] - 0.4, f["inner_h"] - 0.4
    part = cq.Workplane("XY").box(f["width"], f["height"], f["plate"], centered=(True, True, False))
    ring = (cq.Workplane("XY").workplane(offset=-lip).rect(iw, ih).rect(iw - 2 * wall, ih - 2 * wall).extrude(lip))
    part = part.union(ring)
    h = f["bolt_square"] / 2
    up = f["motor_axis_up"]
    part = (part.faces(">Z").workplane(origin=(0, 0, f["plate"]))
            .pushPoints([(h, up + h), (-h, up + h), (h, up - h), (-h, up - h)]).hole(cl))
    # slot for the three motor wires, below the mount
    y_slot = (up - d["printed"]["motor_mount"]["size"] / 2 - ih / 2 - wall) / 2 + wall / 2
    part = part.faces(">Z").workplane(origin=(0, 0, f["plate"])).center(0, y_slot).slot2D(24, 8).cutThruAll()
    return part


def motor_mount(d):
    """
    Thrust wedge between firewall and motor, drawn as seen from the front:
    X = pilot's left, Y up, Z forward (toward the propeller).
    The tilted front face gives right thrust and down thrust, so the THICK
    corner is top-left as the pilot sees it from behind. A notch marks the top.
    """
    m = d["printed"]["motor_mount"]
    cl, head = d["printed"]["m3_clearance"], d["printed"]["m3_head"]
    S, T = m["size"], m["thickness"]
    rt, dn = math.radians(m["right_deg"]), math.radians(m["down_deg"])
    n = cq.Vector(-math.sin(rt), -math.sin(dn), math.cos(rt) * math.cos(dn)).normalized()
    xdir = cq.Vector(0, 1, 0).cross(n).normalized()
    part = cq.Workplane("XY").box(S, S, T + 4, centered=(True, True, False)).edges("|Z").fillet(4)
    cutter = cq.Workplane(cq.Plane(origin=(0, 0, T), xDir=xdir, normal=n)).box(4 * S, 4 * S, 40, centered=(True, True, False))
    part = part.cut(cutter)
    h = m["bolt_square"] / 2
    part = part.faces("<Z").workplane().pushPoints([(h, h), (-h, h), (h, -h), (-h, -h)]).hole(cl)
    part = part.faces("<Z").workplane().hole(10)                       # shaft / circlip clearance
    a, b = m["motor_holes"][0] / 2, m["motor_holes"][1] / 2
    # motor screws go in from the back; heads sit in counterbores
    part = (part.faces("<Z").workplane().pushPoints([(b, 0), (-b, 0), (0, a), (0, -a)])
            .cboreHole(cl, head, T - 5.0))       # 5 mm left: an M3x8 enters the motor 3 mm
    notch = cq.Workplane("XY").circle(2.0).extrude(T + 4).translate((0, S / 2, 0))
    return part.cut(notch)


def wing_joiner(d):
    """V-shaped spar joiner that sets the dihedral. X chordwise, Y spanwise, Z up. Print lying on its side."""
    j = d["printed"]["joiner"]
    side, L = j["side"], j["arm"]
    arm = (cq.Workplane("XY").box(side, side, L, centered=(True, True, False))
           .faces(">Z").workplane().hole(j["bore"], L - 1.5))
    arm = arm.rotate((0, 0, 0), (1, 0, 0), -90)                       # now along +Y
    right = arm.rotate((0, 0, 0), (1, 0, 0), j["dihedral_deg"])       # tip up
    left = right.mirror("XZ")
    return right.union(left)


def _servo_slot_points(sv):
    return sv["body"][0] + 0.4, sv["body"][1] + 0.4, sv["hole_spacing"] / 2


def servo_tray(d):
    """Tray for the elevator and rudder servos. X along the fuselage, Y across. Print plate-down."""
    sv, tr = d["printed"]["servo"], d["printed"]["servo_tray"]
    sl, sw, hs = _servo_slot_points(sv)
    w, L, th = tr["width"], tr["length"], tr["thickness"]
    part = cq.Workplane("XY").box(L, w, th, centered=(True, True, False))
    off = sw / 2 + 4.0
    part = part.faces(">Z").workplane().pushPoints([(0, off), (0, -off)]).rect(sl, sw).cutThruAll()
    part = (part.faces(">Z").workplane()
            .pushPoints([(hs, off), (-hs, off), (hs, -off), (-hs, -off)]).hole(PILOT))
    for sgn in (1, -1):                                               # glue flanges against the fuselage sides
        flange = (cq.Workplane("XY").box(L, 1.6, 8.0, centered=(True, True, False))
                  .translate((0, sgn * (w / 2 - 0.8), th)))
        part = part.union(flange)
    return part


def servo_cradle(d, mirrored=False):
    """
    Cover plate + posts for an aileron servo lying on its side.
    X chordwise (+X aft), Y spanwise (+Y outboard), Z into the wing. Print plate-down.
    The servo drops between the posts; its tabs screw to them; the arm hangs through the slot.
    """
    sv, ws = d["printed"]["servo"], d["wing"]["servo"]
    px, py, pt = ws["plate"]
    body_l, body_w, body_h = sv["body"]
    y0 = -(py - (body_h + 6.0)) / 2 - 1.0                              # plate starts a little inboard of the servo bottom
    part = cq.Workplane("XY").box(px, py, pt, centered=(True, False, False)).translate((0, y0, 0))
    part = part.edges("|Z").fillet(3)
    post_w = (sv["tab_span"] + 4.0 - (body_l + 0.4)) / 2
    for sgn in (1, -1):
        cx = sgn * ((body_l + 0.4) / 2 + post_w / 2)
        post = (cq.Workplane("XY").box(post_w, 2.4, body_w, centered=(True, False, False))
                .translate((cx, sv["tab_height"] - 2.4, pt)))
        hole = (cq.Workplane("XZ").center(sgn * sv["hole_spacing"] / 2, pt + body_w / 2).circle(PILOT / 2)
                .extrude(-60).translate((0, -10, 0)))
        part = part.union(post).cut(hole)
    # slot for the servo arm
    slot = (cq.Workplane("XY").box(18.0, 5.5, 3 * pt, centered=True)
            .translate((ws["shaft_offset"], body_h + 6.0, pt / 2)))
    part = part.cut(slot)
    return part.mirror("XZ") if mirrored else part


def control_horn(d):
    """Glue-on horn. X aft from the hinge line, Y across, Z away from the surface. Print base-down."""
    base = cq.Workplane("XY").box(22, 12, 1.6, centered=(False, True, False)).edges("|Z").fillet(2)
    fin = (cq.Workplane("XZ").polyline([(0, 0), (14, 0), (6, 21), (0, 21)]).close().extrude(2.4)
           .translate((0, 1.2, 1.6)))
    part = base.union(fin)
    for z in (9, 13, 17):
        hole = cq.Workplane("XZ").center(3, 1.6 + z).circle(0.85).extrude(-20).translate((0, -10, 0))
        part = part.cut(hole)
    return part


def gear_block(d):
    """Clamps the landing-gear wire under the fuselage. X along the fuselage, Y across, Z down. Groove side on the bed."""
    g, gb = d["gear"], d["printed"]["gear_block"]
    cl, head = d["printed"]["m3_clearance"], d["printed"]["m3_head"]
    L, Wd, Hh = gb["length"], gb["width"], gb["height"]
    part = cq.Workplane("XY").box(Wd, L, Hh, centered=(True, True, False)).edges("|Z").fillet(2)
    wd = g["wire_d"] + 0.3
    groove = cq.Workplane("XY").box(wd, L + 2, wd, centered=(True, True, False))
    part = part.cut(groove)
    pts = [(sx * (Wd / 2 - 4.5), sy * (L / 2 - 8)) for sx in (1, -1) for sy in (1, -1)]
    part = part.faces(">Z").workplane().pushPoints(pts).cboreHole(cl, head, 3.0)
    return part


def gear_plate(d):
    """Load-spreading plate inside the fuselage floor, opposite the gear block."""
    gb = d["printed"]["gear_block"]
    L, Wd = gb["length"], gb["width"]
    part = cq.Workplane("XY").box(Wd, L, 2.0, centered=(True, True, False)).edges("|Z").fillet(2)
    pts = [(sx * (Wd / 2 - 4.5), sy * (L / 2 - 8)) for sx in (1, -1) for sy in (1, -1)]
    return part.faces(">Z").workplane().pushPoints(pts).hole(d["printed"]["m3_clearance"])


def wheel(d):
    g = d["gear"]
    rad, width = g["wheel_d"] / 2, 12.0
    part = cq.Workplane("XY").circle(rad).extrude(width).edges().fillet(2.5)
    for z0 in (-0.01, width - 3.0):
        pocket = cq.Workplane("XY").workplane(offset=z0).circle(rad - 6).circle(7).extrude(3.01)
        part = part.cut(pocket)
    part = part.faces(">Z").workplane().hole(g["wire_d"] + 0.4)
    part = part.faces(">Z").workplane().polarArray((rad + 1) / 2, 0, 360, 5).hole(9)
    return part


def wheel_collar(d):
    g = d["gear"]
    return cq.Workplane("XY").circle(4.5).extrude(5).faces(">Z").workplane().hole(g["wire_d"] - 0.1)


def dowel_plate(d):
    """Stops the wing-band dowels tearing the foam. Glue one each side where a dowel goes through."""
    f = d["fuselage"]
    return (cq.Workplane("XY").box(22, 22, 1.6, centered=(True, True, False)).edges("|Z").fillet(3)
            .faces(">Z").workplane().hole(f["band_dowel_d"] + 0.3))


def all_parts(d):
    """name -> (solid, quantity, note)"""
    parts = {
        "firewall": (firewall(d), 1, "100% infill"),
        "motor_mount": (motor_mount(d), 1, "100% infill; notch = top, thick side = pilot's left"),
        "wing_joiner": (wing_joiner(d), 1, "print lying on its side, 4 walls"),
        "servo_tray_fuselage": (servo_tray(d), 1, "elevator + rudder servos"),
        "servo_cradle_wing_left": (servo_cradle(d), 1, "left aileron servo"),
        "servo_cradle_wing_right": (servo_cradle(d, mirrored=True), 1, "right aileron servo"),
        "control_horn": (control_horn(d), 4, "2 ailerons, elevator, rudder"),
        "dowel_plate": (dowel_plate(d), 4, "wing band dowels"),
    }
    if d["gear"]:
        parts.update({
            "gear_block": (gear_block(d), 1, "100% infill, groove side on the bed"),
            "gear_plate": (gear_plate(d), 1, "inside the fuselage floor"),
            "wheel": (wheel(d), 2, "3 walls, 15% infill"),
            "wheel_collar": (wheel_collar(d), 4, "press on the axle each side of a wheel"),
        })
    return parts


def print_orientation(name, solid):
    """Rotate each part into the pose it should be printed in (flat face on z = 0)."""
    if name == "wing_joiner":
        solid = solid.rotate((0, 0, 0), (0, 1, 0), 90)
    if name == "firewall":
        solid = solid.rotate((0, 0, 0), (1, 0, 0), 180)                # plate on the bed, lip up
    if name == "gear_block":
        pass                                                           # groove is already at z = 0
    bb = solid.val().BoundingBox()
    return solid.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def main():
    d = load_design()
    out = ROOT / "stl"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.stl"):
        old.unlink()
    bed = d["printed"]["bed"]
    rows, problems = [], []
    for name, (solid, qty, note) in all_parts(d).items():
        solid = print_orientation(name, solid)
        bb = solid.val().BoundingBox()
        size = (bb.xlen, bb.ylen, bb.zlen)
        fits = all(s <= b for s, b in zip(size, bed))
        if not fits:
            problems.append(name)
        cq.exporters.export(solid, str(out / f"{name}.stl"), tolerance=0.02, angularTolerance=0.15)
        mass = solid.val().Volume() * PLA_DENSITY
        rows.append(f"| `{name}.stl` | {qty} | {size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f} | "
                    f"{mass:.1f} | {'yes' if fits else 'NO'} | {note} |")
    text = ("# Print list\n\nGenerated by `cad/printed_parts.py`. PLA, 0.2 mm layers, "
            f"{d['printed']['bed'][0]:.0f} x {d['printed']['bed'][1]:.0f} mm bed. "
            "No supports needed. Mass is for a solid part; real prints are lighter.\n\n"
            "| File | Qty | Size (mm) | Solid mass each (g) | Fits bed | Notes |\n|---|---:|---|---:|---|---|\n"
            + "\n".join(rows) + "\n")
    (out / "PRINT_LIST.md").write_text(text)
    print(text)
    if problems:
        raise SystemExit(f"Parts larger than the printer bed: {problems}")


if __name__ == "__main__":
    main()
