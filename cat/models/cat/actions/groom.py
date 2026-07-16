"""Groom（舔毛）—— 空闲小动作。前爪抬起、头低下、偶尔抖动。"""
from __future__ import annotations

import random

from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand


class GroomAction(Action):
    name = "groom"

    def __init__(self, duration: float | None = None) -> None:
        super().__init__()
        self._duration = duration if duration is not None else random.uniform(2.0, 3.5)
        self._t = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        sprite.pose.grooming = True
        sprite.pose.leg_stride = 0.0
        sprite.pose.tail_wag = 0.3
        sprite.pose.tail_angle = 0.6
        sprite.pose.head_turn = -0.5  # 头低下偏向举起的爪子
        sprite.pose.head_bob = 4.0

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        # 舔的节奏：头部小幅周期性上下
        sprite.pose.head_bob = 4.0 + 2.0 * (abs((self._t * 6.0) % 2 - 1) - 0.5) * 2
        sprite.pose.tail_wag_phase += dt * 3.0
        sprite.pose.eye_open = 0.7
        if self._t >= self._duration:
            reset_to_stand(sprite.pose)
            self.finish()
