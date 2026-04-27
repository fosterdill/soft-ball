from __future__ import annotations

import math


Polygon = list[tuple[float, float]]


def point_in_polygon(px: float, py: float, verts: Polygon) -> bool:
    inside = False
    n = len(verts)
    j = n - 1
    for i in range(n):
        xi, yi = verts[i]
        xj, yj = verts[j]
        if (yi > py) != (yj > py):
            x_int = (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi
            if px < x_int:
                inside = not inside
        j = i
    return inside


def ray_polygon_distance(
    cx: float, cy: float, ux: float, uy: float, verts: Polygon,
) -> float:
    """Distance from (cx, cy) along unit direction (ux, uy) to polygon boundary.

    Returns +inf if the ray misses (shouldn't happen if (cx, cy) is inside).
    """
    best = math.inf
    n = len(verts)
    for i in range(n):
        x1, y1 = verts[i]
        x2, y2 = verts[(i + 1) % n]
        ex = x2 - x1
        ey = y2 - y1
        det = ex * uy - ey * ux
        if abs(det) < 1e-12:
            continue
        wx = x1 - cx
        wy = y1 - cy
        t = (ex * wy - ey * wx) / det
        s = (ux * wy - uy * wx) / det
        if t > 0.0 and 0.0 <= s <= 1.0 and t < best:
            best = t
    return best
