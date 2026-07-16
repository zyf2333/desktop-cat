"""Notice（发现）—— 确认是猎物，压低姿态准备行动。

姿态：身体微压低、瞳孔进一步放大、尾巴尖轻抖。
短暂过渡，结束后进入潜行或直接追（由 State 决定）。
"""
from __future__ import annotations

import math
import random

from cat import config
from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand


class NoticeAction(Action):
    name = "notice"

    def __init__(self, duration: float | None = None) -> None:
        super().__init__()
        self._duration = duration if duration is not None else random.uniform(*config.NOTICE_DURATION_S)
        self._t = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        pose = sprite.pose
        pose.alerted = True
        pose.ear_alert = 1.0
        pose.pupil_dilate = 0.85
        pose.body_squash = 0.2   # 微微压低
        pose.tail_wag = 0.5
        pose.tail_wag_phase = 0.0

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        pose = sprite.pose
        if sprite.mouse_state is not None:
            dx = sprite.mouse_state.pos[0] - sprite.x
            dy = sprite.mouse_state.pos[1] - sprite.y
            d = math.hypot(dx, dy) or 1.0
            pose.pupil_dx = (dx / d) * 0.9
            pose.pupil_dy = (dy / d) * 0.7
        # 尾巴尖快速抖动（兴奋）
        pose.tail_wag_phase += dt * 14.0
        if self._t >= self._duration:
            self.finish()
