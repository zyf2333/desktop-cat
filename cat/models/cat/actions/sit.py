"""Sit（坐）—— 空闲小动作。后腿压低、前爪并拢、尾巴慢摆。"""
from __future__ import annotations

import random

from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand


class SitAction(Action):
    name = "sit"

    def __init__(self, duration: float | None = None) -> None:
        super().__init__()
        self._duration = duration if duration is not None else random.uniform(1.5, 3.0)
        self._t = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        sprite.pose.body_squash = 0.45  # 坐下压扁
        sprite.pose.leg_stride = 0.0
        sprite.pose.tail_wag = 0.3
        sprite.pose.tail_angle = 0.4

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        sprite.pose.tail_wag_phase += dt * 2.0
        # 偶尔眨眼
        cycle = (self._t % 3.0)
        if 2.8 < cycle < 2.95:
            sprite.pose.blink = (2.875 - abs(cycle - 2.875)) * 8
            sprite.pose.blink = max(0.0, min(1.0, sprite.pose.blink))
        else:
            sprite.pose.blink = 0.0
        if self._t >= self._duration:
            reset_to_stand(sprite.pose)
            self.finish()
