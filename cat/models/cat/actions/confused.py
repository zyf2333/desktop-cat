"""Confused（困惑）—— 找不到鼠标时的反应。

姿态：停下、左右张望、歪头、冒问号。
持续一段随机时间后自然结束 → 回到 IDLE（继续干自己的事）。
"""
from __future__ import annotations

import math
import random

from cat import config
from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand


class ConfusedAction(Action):
    name = "confused"

    def __init__(self, duration: float | None = None) -> None:
        super().__init__()
        self._duration = duration if duration is not None else random.uniform(*config.CONFUSED_DURATION_S)
        self._t = 0.0
        self._look_t = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        pose = sprite.pose
        pose.confused = True
        pose.pupil_dilate = 0.3      # 困惑：瞳孔缩小
        pose.ear_alert = 0.4         # 耳朵半竖（还在听）
        pose.tail_wag = 0.2
        pose.leg_stride = 0.0
        pose.body_squash = 0.15      # 微坐

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        self._look_t += dt
        pose = sprite.pose
        # 左右张望：head_turn 在 -1..1 之间缓慢摆动
        pose.head_turn = math.sin(self._look_t * 3.5) * 0.7
        # 歪头：周期性左右歪
        pose.head_tilt = math.sin(self._look_t * 2.0) * 0.25
        # 瞳孔跟随张望方向
        pose.pupil_dx = pose.head_turn * 0.8
        pose.pupil_dy = -0.2
        # 偶尔眨眼
        pose.blink = 1.0 if (self._t % 2.0) > 1.9 else 0.0
        pose.tail_wag_phase += dt * 2.0
        if self._t >= self._duration:
            reset_to_stand(pose)
            self.finish()
