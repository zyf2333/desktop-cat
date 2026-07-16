"""Wrestle（扭打玩）—— PLAYING 状态动作：躺地翻身，四肢乱蹬。

像猫抱着东西扭来扭去玩的姿态。身体翻转（on_back），四肢快速蹬动。
"""
from __future__ import annotations

import math
import random

from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand


class WrestleAction(Action):
    name = "wrestle"

    def __init__(self, target=None, duration: float | None = None) -> None:
        super().__init__()
        self._target = target  # wrestle 不用 target，但接受以统一工厂调用
        self._duration = duration
        self._t = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        d = self._duration
        if d is None:
            # 玩心高的猫扭打更久
            d = random.uniform(1.0, 1.5 + sprite.personality.playfulness * 1.5)
        self._duration = d
        reset_to_stand(sprite.pose)
        pose = sprite.pose
        pose.on_back = True            # 翻身
        pose.body_squash = 0.4
        pose.body_tilt = 1.5           # 大幅倾斜（接近侧翻）
        pose.leg_stride = 1.0          # 四肢乱蹬
        pose.ear_alert = 0.3
        pose.pupil_dilate = 0.5
        pose.mouth = "open"
        pose.tail_wag = 0.8

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        pose = sprite.pose
        # 身体左右扭动
        pose.body_tilt = 1.3 + 0.4 * math.sin(self._t * 8.0)
        # 四肢快速蹬
        pose.leg_phase += dt * 14.0
        # 尾巴兴奋甩
        pose.tail_wag_phase += dt * 18.0
        # 头随扭动转
        pose.head_turn = 0.5 * math.sin(self._t * 6.0)
        if self._t >= self._duration:
            reset_to_stand(pose)
            self.finish()
