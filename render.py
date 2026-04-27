from __future__ import annotations

import math
from typing import NamedTuple

import tcod.console

from ball import SoftBall
from geometry import point_in_polygon, ray_polygon_distance


class Shell(NamedTuple):
    max_norm_radius: float  # outermost normalized r/R this shell covers
    glyph: str
    color: tuple[int, int, int]


# Concentric shells by normalized distance from center. Inner shells get
# bright/heavy ASCII; outer shells get dim/sparse ASCII so the rim looks soft
# and translucent.
SHELLS: list[Shell] = [
    Shell(0.45, "#", (255, 230, 140)),
    Shell(0.70, "o", (220, 175, 80)),
    Shell(0.88, "*", (160, 115, 45)),
    Shell(1.10, ".", (95, 65, 25)),
]


def draw_ball(
    console: tcod.console.Console, ball: SoftBall, width: int, height: int,
) -> None:
    verts = ball.hull()
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    x0 = max(0, int(min(xs)) - 1)
    x1 = min(width - 1, int(max(xs)) + 1)
    y0 = max(0, int(min(ys)) - 1)
    y1 = min(height - 1, int(max(ys)) + 1)

    cx = ball.center.position.x
    cy = ball.center.position.y

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if not point_in_polygon(x + 0.5, y + 0.5, verts):
                continue
            dx = x + 0.5 - cx
            dy = y + 0.5 - cy
            cell_r = math.hypot(dx, dy)
            if cell_r < 1e-6:
                d = 0.0
            else:
                edge_r = ray_polygon_distance(
                    cx, cy, dx / cell_r, dy / cell_r, verts
                )
                d = min(cell_r / edge_r, 1.0) if math.isfinite(edge_r) else 1.0
            for shell in SHELLS:
                if d <= shell.max_norm_radius:
                    console.print(x, y, shell.glyph, fg=shell.color)
                    break
