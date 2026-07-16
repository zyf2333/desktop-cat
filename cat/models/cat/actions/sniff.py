"""Sniff（嗅闻）—— PLAYING 状态动作：贴近鼠标，头上下点嗅闻。

好奇心强的猫更爱做这个。鼻子朝下，头部有节奏地起伏。
"""
from __future__ import annotations

import math
import random

from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand
from cat.utils.geometry import clamp


class SniffAction(Action):
    name = "sniff"

    def __init__(self, target, duration: float | None = None) -> None:
        super().__init__()
        self._target = target
        self._duration = duration
        self._t = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        d = self._duration
        if d is None:
            # 好奇心强的猫嗅更久
            d = random.uniform(0.8, 1.0 + sprite.personality.curiosity * 1.5)
        self._duration = d
        reset_to_stand(sprite.pose)
        pose = sprite.pose
        pose.alerted = True
        pose.ear_alert = 0.6
        pose.pupil_dilate = 0.4
        pose.body_squash = 0.5       # 压低凑近
        pose.leg_stride = 0.0
        pose.head_bob = 6.0          # 头低下
        pose.head_turn = 0.0
        pose.mouth = "open"          # 张嘴嗅
        pose.tail_wag = 0.2

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        pose = sprite.pose
        target = self._target() if callable(self._target) else self._target

        # 缓慢凑近目标（保持贴近但不重叠）
        dx = target[0] - sprite.x
        dy = target[1] - sprite.y
        dist = math.hypot(dx, dy)
        if dist > 30:
            # 慢慢挪过去
            step = 60 * dt
            sprite.x += dx / dist * step
            sprite.y += dy / dist * step
        if abs(dx) > 2:
            sprite.facing = 1 if dx > 0 else -1

        # 头部有节奏地上下嗅（呼吸式）
        pose.head_bob = 6.0 + 3.0 * math.sin(self._t * 10.0)
        # 鼻子抽动（嘴微张合）
        pose.mouth = "open" if math.sin(self._t * 10.0) > 0 else "smile"
        # 耳朵转向目标听
        pose.ear_alert = 0.5 + 0.1 * math.sin(self._t * 8.0)
        pose.tail_wag_phase += dt * 3.0

        if self._t >= self._duration:
            reset_to_stand(pose)
            self.finish()
