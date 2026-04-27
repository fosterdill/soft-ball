from __future__ import annotations

import pymunk

from ball import SoftBall


class Dragger:
    """Mouse drag via PivotJoint with capped force and bias.

    Standard physics-engine drag: the joint pulls the target body toward the
    mouse body, but max_force caps the impulse it can apply per step and
    max_bias caps how fast it can correct positional error. Together these
    make the latch-on smooth (no instant yank) and the follow snappy without
    spazzing on fast mouse motion.

    Throw on release is automatic — the target body keeps whatever velocity
    the joint had been imparting.
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
        # Drag the center body, not a perimeter point. The anchor offset below
        # keeps the cursor on the click point; using the center as the target
        # means the whole ball tracks the cursor coherently instead of one rim
        # point being yanked while the rest lags behind.
        self.target = ball.center
        # Anchor the joint at the click offset in the target's local frame so
        # the original click point on the body stays under the cursor (no snap
        # to body center / rim).
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
