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
        perimeter_mass: float = 0.28,
        radial_stiffness: float = 55.0,
        radial_damping: float = 3.0,
        rim_stiffness: float = 220.0,
        rim_damping: float = 4.5,
        cross_stiffness: float = 80.0,
        cross_damping: float = 3.0,
        pressure_k: float = 1700.0,
        tangential_damping: float = 3.0,
        elasticity: float = 0.92,
    ) -> None:
        self.space = space
        self.radius = radius
        self.n = n
        self.pressure_k = pressure_k
        self.tangential_damping = tangential_damping
        # Area of the regular n-gon at rest. Pressure pushes us back toward this.
        self.rest_area = 0.5 * n * radius * radius * math.sin(2 * math.pi / n)

        self.center = pymunk.Body(mass=center_mass, moment=float("inf"))
        self.center.position = cx, cy
        space.add(self.center)

        self.perimeter: list[pymunk.Body] = []
        for i in range(n):
            angle = 2 * math.pi * i / n
            body = pymunk.Body(mass=perimeter_mass, moment=float("inf"))
            body.position = (
                cx + radius * math.cos(angle),
                cy + radius * math.sin(angle),
            )
            shape = pymunk.Circle(body, 0.7)
            shape.elasticity = elasticity
            shape.friction = 0.0
            space.add(body, shape)
            self.perimeter.append(body)

        # Radial springs: each perimeter point ↔ center.
        for b in self.perimeter:
            self._add_spring(self.center, b, radius, radial_stiffness, radial_damping)

        # Rim springs: each perimeter point ↔ next perimeter point.
        rim_rest = 2 * radius * math.sin(math.pi / n)
        for i in range(n):
            self._add_spring(
                self.perimeter[i], self.perimeter[(i + 1) % n],
                rim_rest, rim_stiffness, rim_damping,
            )

        # Cross springs (across the diameter) — keeps the ball from collapsing
        # into a pancake when it slams into a wall.
        for i in range(n // 2):
            self._add_spring(
                self.perimeter[i], self.perimeter[i + n // 2],
                2 * radius, cross_stiffness, cross_damping,
            )

    def _add_spring(
        self, a: pymunk.Body, b: pymunk.Body,
        rest_length: float, stiffness: float, damping: float,
    ) -> None:
        self.space.add(pymunk.DampedSpring(
            a, b, (0, 0), (0, 0),
            rest_length=rest_length, stiffness=stiffness, damping=damping,
        ))

    def kick(self, vx: float, vy: float) -> None:
        self.center.velocity = (vx, vy)
        for b in self.perimeter:
            b.velocity = (vx, vy)

    def hull(self) -> list[tuple[float, float]]:
        return [(b.position.x, b.position.y) for b in self.perimeter]

    def pre_step(self) -> None:
        """Apply gas-pressure and tangential damping. Call before space.step()."""
        self._apply_tangential_damping()
        self._apply_pressure()

    def _apply_tangential_damping(self) -> None:
        """Damp perimeter motion that's tangent to the radial direction.

        The springs in this body don't resist the perimeter ring rotating
        around the center as a rigid set — radial springs only fight radial
        motion, and rim/cross spring lengths are invariant under uniform
        rotation. Without this damping, any angular momentum the perimeter
        picks up (e.g. from an asymmetric wall hit) persists indefinitely,
        making the ball wobble along its path. Radial motion (the kind that
        drag and bounce deformation use) is intentionally untouched.
        """
        if self.tangential_damping <= 0:
            return
        cx, cy = self.center.position
        cvx, cvy = self.center.velocity
        c = self.tangential_damping
        for b in self.perimeter:
            dx = b.position.x - cx
            dy = b.position.y - cy
            r2 = dx * dx + dy * dy
            if r2 < 1e-6:
                continue
            r = math.sqrt(r2)
            tx = -dy / r
            ty = dx / r
            rvx = b.velocity.x - cvx
            rvy = b.velocity.y - cvy
            v_tan = rvx * tx + rvy * ty
            fmag = -c * v_tan
            b.apply_force_at_local_point((fmag * tx, fmag * ty), (0, 0))

    def _apply_pressure(self) -> None:
        """Push the perimeter outward when the polygon area is below rest."""
        n = self.n
        verts = [(b.position.x, b.position.y) for b in self.perimeter]

        # Signed shoelace area; sign tells us polygon winding so we can pick
        # the outward normal direction.
        signed_area = 0.0
        for i in range(n):
            x1, y1 = verts[i]
            x2, y2 = verts[(i + 1) % n]
            signed_area += x1 * y2 - x2 * y1
        signed_area *= 0.5
        abs_area = abs(signed_area)
        if abs_area < 1e-6:
            return

        deficit = self.rest_area - abs_area
        if deficit <= 0:
            return  # over-inflated → let springs handle it; pressure only pushes out
        pressure = self.pressure_k * deficit / abs_area
        winding = 1.0 if signed_area > 0 else -1.0

        for i in range(n):
            a = self.perimeter[i]
            b = self.perimeter[(i + 1) % n]
            ex = b.position.x - a.position.x
            ey = b.position.y - a.position.y
            # Outward normal scaled by edge length: (ey, -ex) for CCW (winding>0).
            # Pressure force on this edge = pressure * length * unit_normal,
            # which equals pressure * (ey, -ex) since (ey, -ex) already has
            # length=edge_len. Split half-and-half between the two endpoints.
            fx = pressure * ey * winding * 0.5
            fy = -pressure * ex * winding * 0.5
            a.apply_force_at_local_point((fx, fy), (0, 0))
            b.apply_force_at_local_point((fx, fy), (0, 0))
