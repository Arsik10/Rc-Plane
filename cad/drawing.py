"""
Tiny 2D drawing model for the foam templates.

A Sheet collects lines in millimetres (x right, y up) and writes
  * an SVG at true size, and
  * a PDF tiled over A4 pages with overlap and alignment marks.

Line kinds
  cut    solid, cut right through
  fold   long dashes, score / fold line
  bevel  dash-dot, hinge line: cut half through and bevel
  mark   thin, just a position mark to draw on the foam
"""
import math
from xml.sax.saxutils import escape

STYLE = {
    "cut":   dict(color="#111111", width=0.45, dash=None),
    "fold":  dict(color="#1565c0", width=0.35, dash=(6, 3)),
    "bevel": dict(color="#c62828", width=0.35, dash=(8, 2, 1.5, 2)),
    "mark":  dict(color="#555555", width=0.2, dash=(1.5, 1.5)),
    "dim":   dict(color="#555555", width=0.2, dash=None),
}
LEGEND = [("cut", "cut through"), ("fold", "score and fold"), ("bevel", "hinge: cut half through, bevel"),
          ("mark", "position mark only")]


class Sheet:
    def __init__(self, name, title, note=""):
        self.name, self.title, self.note = name, title, note
        self.paths, self.circles, self.texts = [], [], []

    # ---- primitives ------------------------------------------------------
    def poly(self, pts, kind="cut", closed=True):
        self.paths.append(([(float(x), float(y)) for x, y in pts], kind, closed))

    def line(self, p1, p2, kind="mark"):
        self.poly([p1, p2], kind, closed=False)

    def rect(self, x0, y0, x1, y1, kind="cut"):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], kind)

    def circle(self, c, radius, kind="cut"):
        self.circles.append((float(c[0]), float(c[1]), float(radius), kind))

    def text(self, p, s, size=4.0, anchor="start", angle=0):
        self.texts.append((float(p[0]), float(p[1]), str(s), float(size), anchor, angle))

    def dim(self, p1, p2, label=None, offset=8.0, size=3.5):
        """Dimension line between two points, offset to the left of p1->p2."""
        (x1, y1), (x2, y2) = p1, p2
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 1e-6:
            return
        nx, ny = -(y2 - y1) / L, (x2 - x1) / L
        a, b = (x1 + nx * offset, y1 + ny * offset), (x2 + nx * offset, y2 + ny * offset)
        self.line(a, b, "dim")
        for p, q in ((p1, a), (p2, b)):
            self.line(p, (q[0] + nx * 1.5, q[1] + ny * 1.5), "dim")
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        if ang > 90 or ang <= -90:
            ang += 180
        mx, my = (a[0] + b[0]) / 2 + nx * 1.2, (a[1] + b[1]) / 2 + ny * 1.2
        self.text((mx, my), label or f"{L:.0f}", size, "middle", ang)

    def bounds(self, pad=0.0):
        xs, ys = [], []
        for pts, _, _ in self.paths:
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts]
        for x, y, rad, _ in self.circles:
            xs += [x - rad, x + rad]
            ys += [y - rad, y + rad]
        for x, y, s, size, anchor, ang in self.texts:
            w = 0.55 * size * len(s)
            if ang:
                xs += [x - size, x + size]
                ys += [y - w / 2, y + w / 2]
            else:
                x0 = x - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
                xs += [x0, x0 + w]
                ys += [y - 0.3 * size, y + size]
        return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad

    # ---- SVG -------------------------------------------------------------
    def svg(self, pad=6.0, scale=1.0, classes_only=False):
        x0, y0, x1, y1 = self.bounds(pad)
        w, h = x1 - x0, y1 - y0
        fy = lambda y: y1 - y                                      # noqa: E731
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * scale:.2f}mm" height="{h * scale:.2f}mm" '
               f'viewBox="{x0:.2f} 0 {w:.2f} {h:.2f}" role="img" aria-label="{escape(self.title)}">']
        if not classes_only:
            css = "".join(
                f".{k}{{fill:none;stroke:{v['color']};stroke-width:{v['width']};"
                + (f"stroke-dasharray:{' '.join(map(str, v['dash']))};" if v["dash"] else "") + "}"
                for k, v in STYLE.items())
            out.append(f"<style>{css}text{{font-family:Helvetica,Arial,sans-serif;fill:#111}}</style>")
        for pts, kind, closed in self.paths:
            dstr = "M" + " L".join(f"{x:.2f} {fy(y):.2f}" for x, y in pts) + (" Z" if closed else "")
            out.append(f'<path class="{kind}" d="{dstr}"/>')
        for x, y, rad, kind in self.circles:
            out.append(f'<circle class="{kind}" cx="{x:.2f}" cy="{fy(y):.2f}" r="{rad:.2f}"/>')
        for x, y, s, size, anchor, ang in self.texts:
            rot = f' transform="rotate({-ang:.1f} {x:.2f} {fy(y):.2f})"' if ang else ""
            out.append(f'<text x="{x:.2f}" y="{fy(y):.2f}" font-size="{size}" text-anchor="{anchor}"{rot}>'
                       f"{escape(s)}</text>")
        out.append("</svg>")
        return "\n".join(out)

    # ---- tiled PDF -------------------------------------------------------
    def pdf(self, path, margin=10.0, overlap=10.0):
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor

        x0, y0, x1, y1 = self.bounds(4.0)
        W, H = x1 - x0, y1 - y0
        header = 9.0                                   # strip for the page label

        def grid(pw, ph):
            uw, uh = pw - 2 * margin, ph - 2 * margin - header
            nx = max(1, math.ceil((W - overlap) / (uw - overlap)))
            ny = max(1, math.ceil((H - overlap) / (uh - overlap)))
            return nx, ny, uw, uh

        portrait, land = (210.0, 297.0), (297.0, 210.0)
        gp, gl = grid(*portrait), grid(*land)
        (pw, ph), (nx, ny, uw, uh) = (portrait, gp) if gp[0] * gp[1] <= gl[0] * gl[1] else (land, gl)
        cv = canvas.Canvas(str(path), pagesize=(pw * mm, ph * mm))
        cv.setTitle(self.title)
        for j in range(ny):                            # rows, top to bottom
            for i in range(nx):
                tx = x0 + i * (uw - overlap)
                ty = y1 - uh - j * (uh - overlap)       # lower edge of this tile
                cv.saveState()
                # header
                cv.setFont("Helvetica-Bold", 9)
                cv.drawString(margin * mm, (ph - margin - 5) * mm, self.title)
                cv.setFont("Helvetica", 8)
                cv.drawRightString((pw - margin) * mm, (ph - margin - 5) * mm,
                                   f"sheet {j * nx + i + 1} of {nx * ny}   row {j + 1}/{ny}  column {i + 1}/{nx}"
                                   "   print at 100% (no scaling)")
                # tile frame + alignment crosses in the overlap corners
                cv.setStrokeColor(HexColor("#999999"))
                cv.setLineWidth(0.3)
                cv.setDash(2, 2)
                cv.rect(margin * mm, margin * mm, uw * mm, uh * mm)
                cv.setDash()
                for cx in (margin + overlap / 2, margin + uw - overlap / 2):
                    for cy in (margin + overlap / 2, margin + uh - overlap / 2):
                        cv.line((cx - 3) * mm, cy * mm, (cx + 3) * mm, cy * mm)
                        cv.line(cx * mm, (cy - 3) * mm, cx * mm, (cy + 3) * mm)
                        cv.circle(cx * mm, cy * mm, 1.5 * mm)
                # clip to the tile and draw the template
                clip = cv.beginPath()
                clip.rect(margin * mm, margin * mm, uw * mm, uh * mm)
                cv.clipPath(clip, stroke=0, fill=0)
                cv.translate((margin - tx) * mm, (margin - ty) * mm)
                # 50 mm check square, bottom-left of every tile
                cv.setStrokeColor(HexColor("#2e7d32"))
                cv.setLineWidth(0.25)
                sx, sy = tx + overlap + 2, ty + overlap + 2
                if nx * ny > 1 or (W > 70 and H > 70):
                    cv.rect(sx * mm, sy * mm, 50 * mm, 50 * mm)
                    cv.setFont("Helvetica", 6)
                    cv.setFillColor(HexColor("#2e7d32"))
                    cv.drawString((sx + 1.5) * mm, (sy + 1.5) * mm, "check: this square is 50 x 50 mm")
                for pts, kind, closed in self.paths:
                    st = STYLE[kind]
                    cv.setStrokeColor(HexColor(st["color"]))
                    cv.setLineWidth(st["width"] * mm)
                    cv.setDash([v * mm for v in st["dash"]] if st["dash"] else [])
                    pth = cv.beginPath()
                    pth.moveTo(pts[0][0] * mm, pts[0][1] * mm)
                    for x, y in pts[1:]:
                        pth.lineTo(x * mm, y * mm)
                    if closed:
                        pth.close()
                    cv.drawPath(pth, stroke=1, fill=0)
                for x, y, rad, kind in self.circles:
                    st = STYLE[kind]
                    cv.setStrokeColor(HexColor(st["color"]))
                    cv.setLineWidth(st["width"] * mm)
                    cv.setDash([v * mm for v in st["dash"]] if st["dash"] else [])
                    cv.circle(x * mm, y * mm, rad * mm)
                cv.setDash()
                cv.setFillColor(HexColor("#111111"))
                for x, y, s, size, anchor, ang in self.texts:
                    cv.saveState()
                    cv.translate(x * mm, y * mm)
                    if ang:
                        cv.rotate(ang)
                    cv.setFont("Helvetica", size * mm)
                    {"start": cv.drawString, "middle": cv.drawCentredString, "end": cv.drawRightString}[anchor](0, 0, s)
                    cv.restoreState()
                cv.restoreState()
                cv.showPage()
        cv.save()
        return nx * ny
