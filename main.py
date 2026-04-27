from __future__ import annotations

import time

import pymunk
import tcod.console
import tcod.context
import tcod.event
import tcod.tileset

from ball import SoftBall
from drag import Dragger
from geometry import point_in_polygon
from render import draw_ball

WIDTH, HEIGHT = 120, 80
# Square cells so circles look round (no aspect compensation needed).
FONT_PATH = "/System/Library/Fonts/Monaco.ttf"
CELL = 12
PHYSICS_DT = 1.0 / 240.0


def make_walls(space: pymunk.Space, w: int, h: int) -> None:
    pad = 0.5
    corners = [(pad, pad), (w - pad, pad), (w - pad, h - pad), (pad, h - pad)]
    for i in range(4):
        wall = pymunk.Segment(
            space.static_body, corners[i], corners[(i + 1) % 4], 0.2,
        )
        wall.elasticity = 1.0
        wall.friction = 0.0
        space.add(wall)


def load_tileset() -> tcod.tileset.Tileset | None:
    try:
        return tcod.tileset.load_truetype_font(FONT_PATH, CELL, CELL)
    except RuntimeError:
        return None


def handle_event(
    event: tcod.event.Event,
    context: tcod.context.Context,
    ball: SoftBall,
    drag: Dragger,
) -> None:
    if isinstance(event, tcod.event.Quit):
        raise SystemExit()
    if isinstance(event, tcod.event.KeyDown):
        if event.sym == tcod.event.KeySym.ESCAPE:
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


def main() -> None:
    space = pymunk.Space()
    space.gravity = (0.0, 0.0)
    space.damping = 1.0
    make_walls(space, WIDTH, HEIGHT)

    ball = SoftBall(space, WIDTH / 2, HEIGHT / 2, radius=10.0, n=24)
    ball.kick(28.0, 18.0)
    drag = Dragger(space)

    console = tcod.console.Console(WIDTH, HEIGHT)
    with tcod.context.new(
        columns=WIDTH,
        rows=HEIGHT,
        tileset=load_tileset(),
        title="Soft Ball",
        vsync=True,
    ) as context:
        last = time.perf_counter()
        accumulator = 0.0
        while True:
            now = time.perf_counter()
            accumulator += min(now - last, 0.1)
            last = now
            while accumulator >= PHYSICS_DT:
                ball.pre_step()
                space.step(PHYSICS_DT)
                accumulator -= PHYSICS_DT

            console.clear()
            draw_ball(console, ball, WIDTH, HEIGHT)
            context.present(console)

            for event in tcod.event.get():
                handle_event(event, context, ball, drag)


if __name__ == "__main__":
    main()
