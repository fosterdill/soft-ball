from __future__ import annotations

import math

import pymunk


class SoftBall:
    """A 2D mass-spring soft body: ring of perimeter masses + a central mass.

    All deformation is emergent — the springs and the perimeter circles'
    collisions with walls are the only things controlling shape.
    """

    def __init__(
        self,
        space: pymunk.Space,
        cx: float,
        cy: float,
        radius: float = 5.0,
        n: int = 18,
        center_mass: float = 2.0,
        perimeter_mass: float = 0.18,
        radial_stiffness: float = 220.0,
        radial_damping: float = 3.5,
        rim_stiffness: float = 220.0,
        rim_damping: float = 3.5,
        cross_stiffness: float = 70.0,
        cross_damping: float = 2.5,
        elasticity: float = 0.92,
    ) -> None:
        self.radius = radius
        self.n = n

        self.center = pymunk.Body(mass=center_mass, moment=float("inf"))
        self.center.position = cx, cy
        space.add(self.center)

        self.perimeter: list[pymunk.Body] = []
        for i in range(n):
            angle = 2 * math.pi * i / n
            body = pymunk.Body(mass=perimeter_mass, moment=float("inf"))
            body.position = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
            shape = pymunk.Circle(body, 0.45)
            shape.elasticity = elasticity
            shape.friction = 0.0
            space.add(body, shape)
            self.perimeter.append(body)

        for b in self.perimeter:
            space.add(pymunk.DampedSpring(
                self.center, b, (0, 0), (0, 0),
                rest_length=radius,
                stiffness=radial_stiffness,
                damping=radial_damping,
            ))

        rim_rest = 2 * radius * math.sin(math.pi / n)
        for i in range(n):
            a = self.perimeter[i]
            b = self.perimeter[(i + 1) % n]
            space.add(pymunk.DampedSpring(
                a, b, (0, 0), (0, 0),
                rest_length=rim_rest,
                stiffness=rim_stiffness,
                damping=rim_damping,
            ))

        # Cross springs (across the diameter) — keeps the ball from collapsing
        # into a pancake when it slams into a wall.
        for i in range(n // 2):
            a = self.perimeter[i]
            b = self.perimeter[i + n // 2]
            space.add(pymunk.DampedSpring(
                a, b, (0, 0), (0, 0),
                rest_length=2 * radius,
                stiffness=cross_stiffness,
                damping=cross_damping,
            ))

    def kick(self, vx: float, vy: float) -> None:
        self.center.velocity = (vx, vy)
        for b in self.perimeter:
            b.velocity = (vx, vy)

    def closest_perimeter(self, x: float, y: float) -> pymunk.Body:
        return min(
            self.perimeter,
            key=lambda b: (b.position.x - x) ** 2 + (b.position.y - y) ** 2,
        )

    def hull(self) -> list[tuple[float, float]]:
        return [(b.position.x, b.position.y) for b in self.perimeter]
