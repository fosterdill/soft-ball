from __future__ import annotations

import pymunk

from ball import SoftBall


class Dragger:
    """Connects a kinematic 'mouse body' to the ball with a damped spring.

    Throw velocity on release is whatever momentum the spring transferred to
    the dragged body — no manual velocity tracking needed.
    """

    def __init__(self, space: pymunk.Space, stiffness: float = 260.0, damping: float = 12.0):
        self.space = space
        self.stiffness = stiffness
        self.damping = damping
        self.mouse_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.spring: pymunk.DampedSpring | None = None
        self.target: pymunk.Body | None = None

    @property
    def active(self) -> bool:
        return self.spring is not None

    def begin(self, ball: SoftBall, mx: float, my: float) -> None:
        self.mouse_body.position = mx, my
        self.target = ball.closest_perimeter(mx, my)
        self.spring = pymunk.DampedSpring(
            self.mouse_body, self.target, (0, 0), (0, 0),
            rest_length=0.0,
            stiffness=self.stiffness,
            damping=self.damping,
        )
        self.space.add(self.spring)

    def motion(self, mx: float, my: float) -> None:
        self.mouse_body.position = mx, my

    def end(self) -> None:
        if self.spring is not None:
            self.space.remove(self.spring)
            self.spring = None
            self.target = None
