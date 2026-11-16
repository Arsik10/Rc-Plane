"""
Clark Y airfoil and the foam-board section that is actually built.

Coordinates are the classic Clark Y ordinates (percent of chord, measured
from the flat-bottom reference line).
"""
import numpy as np
from shapely.geometry import Polygon, box

_X = np.array([0, 1.25, 2.5, 5, 7.5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]) / 100
_UP = np.array([3.50, 5.45, 6.50, 7.90, 8.85, 9.60, 10.68, 11.36, 11.70, 11.40,
                10.52, 9.15, 7.35, 5.22, 2.80, 1.49, 0.12]) / 100
_LO = np.array([3.50, 1.93, 1.47, 0.93, 0.63, 0.42, 0.15, 0.03, 0, 0, 0, 0, 0, 0, 0, 0, 0]) / 100


def _pchip(xk, yk, x):
    """Monotone cubic interpolation (Fritsch-Carlson), numpy only."""
    xk, yk, x = np.asarray(xk, float), np.asarray(yk, float), np.asarray(x, float)
    h = np.diff(xk)
    d = np.diff(yk) / h
    m = np.zeros_like(yk)
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, len(yk) - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    i = np.clip(np.searchsorted(xk, x) - 1, 0, len(xk) - 2)
    t = (x - xk[i]) / h[i]
    h00, h10 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t
    h01, h11 = -2 * t**3 + 3 * t**2, t**3 - t**2
    return h00 * yk[i] + h10 * h[i] * m[i] + h01 * yk[i + 1] + h11 * h[i] * m[i + 1]


def upper(xf):
    """Upper-surface height (fraction of chord) at chord fraction xf."""
    # interpolating against sqrt(x) keeps the round nose smooth
    return _pchip(np.sqrt(_X), _UP, np.sqrt(np.clip(xf, 0, 1)))


def lower(xf):
    return _pchip(np.sqrt(_X), _LO, np.sqrt(np.clip(xf, 0, 1)))


def _stations(n):
    """Chord fractions, bunched at the nose."""
    return (1 - np.cos(np.linspace(0, np.pi, n))) / 2


def true_profile(chord, n=70):
    """Closed polygon of the real Clark Y: TE -> over the top -> LE -> bottom."""
    xs = _stations(n)
    top = [(x * chord, upper(x) * chord) for x in xs[::-1]]
    bot = [(x * chord, lower(x) * chord) for x in xs[1:]]
    return top + bot


def selig_dat(n=60):
    """Clark Y in Selig .dat format (for XFLR5 / XFOIL)."""
    xs = _stations(n)
    rows = [(x, float(upper(x))) for x in xs[::-1]] + [(x, float(lower(x))) for x in xs[1:]]
    return "CLARK Y\n" + "\n".join(f"{x:.6f} {y:.6f}" for x, y in rows) + "\n"


def top_skin_outline(chord, t, hinge_frac, flat_from, n=60):
    """
    Outer surface of the folded top skin as a polyline of (x, z).

    Starts at the bottom of the nose (0, 0), climbs the nose, follows the
    Clark Y upper surface to `flat_from`, then runs straight to the point
    where the skin lands on the bottom plate at the hinge line: (hinge, 2t).
    """
    xs = _stations(n) * flat_from
    pts = [(0.0, 0.0)] + [(x * chord, float(upper(x)) * chord) for x in xs]
    pts.append((hinge_frac * chord, 2 * t))
    return pts


def polyline_length(pts):
    p = np.asarray(pts)
    return float(np.sum(np.hypot(*np.diff(p, axis=0).T)))


def arc_position(pts, x_target):
    """Distance along the polyline to the first point whose x reaches x_target."""
    s = 0.0
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        seg = float(np.hypot(x1 - x0, z1 - z0))
        if x1 >= x_target > x0:
            return s + seg * (x_target - x0) / (x1 - x0)
        s += seg
    return s


def foam_section(chord, t, hinge_frac, flat_from):
    """As-built outer section: folded skin in front, single plate behind the hinge."""
    top = top_skin_outline(chord, t, hinge_frac, flat_from)
    xh = hinge_frac * chord
    return Polygon(top + [(xh, t), (chord, t), (chord, 0.0)])


def rib_polygon(chord, t, hinge_frac, flat_from, min_height=2.5):
    """
    Rib = the space between the bottom plate and the top skin.
    Returns a shapely polygon in section coordinates (x aft, z up).
    """
    top = top_skin_outline(chord, t, hinge_frac, flat_from)
    xh = hinge_frac * chord
    shell = Polygon(top + [(xh, 0.0)])
    inner = shell.buffer(-t, join_style=2)
    # trim the crushed nose and the thin tail where the skin lands
    slope = (top[-2][1] - 2 * t) / (xh - top[-2][0])
    x_end = xh - (min_height + t * (np.sqrt(1 + slope**2) - 1)) / slope
    inner = inner.intersection(box(t + 3.0, t, x_end, chord))
    if inner.geom_type != "Polygon":
        inner = max(inner.geoms, key=lambda g: g.area)
    return inner


def inner_height(rib, x):
    """(z_low, z_high) of the rib at chordwise position x."""
    from shapely.geometry import LineString
    hit = rib.intersection(LineString([(x, -1e3), (x, 1e3)]))
    zs = [c[1] for c in hit.coords]
    return min(zs), max(zs)
