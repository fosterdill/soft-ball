# soft-ball

A bouncing soft-body ball rendered in the terminal with libtcod, simulated with
pymunk. The ball is a ring of perimeter masses tied to a central mass with
radial, rim, and cross springs, plus a gas-pressure term that pushes the
polygon back toward its rest area. All deformation is emergent — only the
springs and the perimeter circles' wall collisions shape it.

## Run

```sh
uv sync
uv run python main.py
```

Requires Python 3.10+. On macOS the renderer loads
`/System/Library/Fonts/Monaco.ttf` for square cells; on other platforms it
falls back to libtcod's default tileset.

## Controls

- **Left-click + drag** — grab the ball; release to throw.
- **Esc** — quit.

## Layout

| File          | Role                                                       |
| ------------- | ---------------------------------------------------------- |
| `main.py`     | Window setup, physics step loop, event dispatch.           |
| `ball.py`     | `SoftBall` — masses, springs, pressure, tangential damping.|
| `drag.py`     | `Dragger` — mouse-follow `PivotJoint` with capped force.   |
| `render.py`   | Concentric ASCII shells shaded by depth from the center.   |
| `geometry.py` | `point_in_polygon`, `ray_polygon_distance`.                |
