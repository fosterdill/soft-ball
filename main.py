from __future__ import annotations

import time

import pymunk
import tcod
import tcod.console
import tcod.context
import tcod.event
import tcod.tileset

from ball import SoftBall
from drag import Dragger

WIDTH, HEIGHT = 60, 40
# Square 16x16 cells so circles look round (no aspect compensation needed).
FONT_PATH = "/System/Library/Fonts/Monaco.ttf"
CELL = 16

PHYSICS_DT = 1.0 / 240.0
GLYPH = "█"
BALL_COLOR = (255, 200, 0)


def make_walls(space: pymunk.Space, w: int, h: int) -> None:
    pad = 0.5
    corners = [(pad, pad), (w - pad, pad), (w - pad, h - pad), (pad, h - pad)]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        wall = pymunk.Segment(space.static_body, a, b, 0.2)
        wall.elasticity = 1.0
        wall.friction = 0.0
        space.add(wall)


def point_in_polygon(px: float, py: float, verts: list[tuple[float, float]]) -> bool:
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


def draw_ball(console: tcod.console.Console, ball: SoftBall) -> None:
    verts = ball.hull()
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    x0 = max(0, int(min(xs)) - 1)
    x1 = min(WIDTH - 1, int(max(xs)) + 1)
    y0 = max(0, int(min(ys)) - 1)
    y1 = min(HEIGHT - 1, int(max(ys)) + 1)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if point_in_polygon(x + 0.5, y + 0.5, verts):
                console.print(x, y, GLYPH, fg=BALL_COLOR)


def main() -> None:
    space = pymunk.Space()
    space.gravity = (0.0, 0.0)
    space.damping = 1.0

    make_walls(space, WIDTH, HEIGHT)
    ball = SoftBall(space, WIDTH / 2, HEIGHT / 2, radius=5.0, n=18)
    ball.kick(20.0, 13.0)

    drag = Dragger(space)
    console = tcod.console.Console(WIDTH, HEIGHT)

    try:
        tileset = tcod.tileset.load_truetype_font(FONT_PATH, CELL, CELL)
    except RuntimeError:
        tileset = None

    with tcod.context.new(
        columns=WIDTH,
        rows=HEIGHT,
        tileset=tileset,
        title="Soft Ball",
        vsync=True,
    ) as context:
        last = time.perf_counter()
        accumulator = 0.0
        while True:
            now = time.perf_counter()
            frame_dt = min(now - last, 0.1)
            last = now

            accumulator += frame_dt
            while accumulator >= PHYSICS_DT:
                space.step(PHYSICS_DT)
                accumulator -= PHYSICS_DT

            console.clear()
            draw_ball(console, ball)
            context.present(console)

            for event in tcod.event.get():
                if isinstance(event, tcod.event.Quit):
                    raise SystemExit()
                elif isinstance(event, tcod.event.MouseButtonDown):
                    if event.button == tcod.event.MouseButton.LEFT:
                        tx, ty = context.pixel_to_tile(*event.position)
                        if point_in_polygon(tx, ty, ball.hull()):
                            drag.begin(ball, tx, ty)
                elif isinstance(event, tcod.event.MouseButtonUp):
                    if event.button == tcod.event.MouseButton.LEFT and drag.active:
                        drag.end()
                elif isinstance(event, tcod.event.MouseMotion):
                    if drag.active:
                        tx, ty = context.pixel_to_tile(*event.position)
                        drag.motion(tx, ty)
                elif isinstance(event, tcod.event.KeyDown):
                    if event.sym == tcod.event.KeySym.ESCAPE:
                        raise SystemExit()


if __name__ == "__main__":
    main()
