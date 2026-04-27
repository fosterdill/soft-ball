from __future__ import annotations

import pymunk

from ball import SoftBall


class Dragger:
    """Mouse drag via PivotJoint with capped force and bias.

    max_force caps the per-step impulse so latch-on doesn't yank the body;
    max_bias caps positional-error correction so fast mouse motion doesn't
    make the body spaz. Throw on release is automatic — the body keeps
    whatever velocity the joint was imparting.
    """

    def __init__(
        self,
        space: pymunk.Space,
        max_force: float = 5000.0,
        max_bias: float = 300.0,
    ):
        self.space = space
        self.max_force = max_force
        self.max_bias = max_bias
        self.mouse_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.joint: pymunk.PivotJoint | None = None
        self.target: pymunk.Body | None = None

    @property
    def active(self) -> bool:
        return self.joint is not None

    def begin(self, ball: SoftBall, mx: float, my: float) -> None:
        self.mouse_body.position = mx, my
        # Target the center (so the whole ball tracks coherently instead of one
        # rim point being yanked) but anchor at the click offset (so the click
        # point stays under the cursor — no snap to body center).
        self.target = ball.center
        anchor = (mx - self.target.position.x, my - self.target.position.y)
        self.joint = pymunk.PivotJoint(
            self.mouse_body, self.target, (0, 0), anchor
        )
        self.joint.max_force = self.max_force
        self.joint.max_bias = self.max_bias
        self.space.add(self.joint)

    def motion(self, mx: float, my: float) -> None:
        self.mouse_body.position = mx, my

    def end(self) -> None:
        if self.joint is not None:
            self.space.remove(self.joint)
            self.joint = None
            self.target = None
