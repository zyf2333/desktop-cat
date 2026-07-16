"""JumpPounce（跳扑）—— PLAYING 状态动作：高高跳起扑向鼠标。

比 PounceAction 更高更夸张（body_lift 大），是猫兴奋到极致的扑击。
落地后短暂回弹。
"""
from __future__ import annotations

import math

from cat import config
from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand
from cat.utils.geometry import clamp, ease_out_cubic


class JumpPounceAction(Action):
    name = "jump_pounce"

    def __init__(self, target) -> None:
        super().__init__()
        self._target = target
        self._t = 0.0
        self._phase = "jump"  # jump -> land -> recover

    def start(self, sprite) -> None:
        super().start(sprite)
        # 锁定目标
        self._target = self._target() if callable(self._target) else self._target
        self._start_pos = (sprite.x, sprite.y)
        # 限制跳扑距离（比 pounce 短，因为是玩）
        d = math.hypot(self._target[0] - sprite.x, self._target[1] - sprite.y)
        max_d = 130
        if d > max_d:
            ux = (self._target[0] - sprite.x) / d
            uy = (self._target[1] - sprite.y) / d
            self._target = (sprite.x + ux * max_d, sprite.y + uy * max_d)
        if self._target[0] >= sprite.x:
            sprite.facing = 1
        else:
            sprite.facing = -1
        self._jump_time = 0.45
        self._land_time = 0.18
        reset_to_stand(sprite.pose)
        pose = sprite.pose
        pose.alerted = True
        pose.ear_alert = 1.0
        pose.pupil_dilate = 1.0
        pose.mouth = "open"

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        pose = sprite.pose

        if self._phase == "jump":
            p = clamp(self._t / self._jump_time, 0.0, 1.0)
            ep = ease_out_cubic(p)
            sprite.x = self._start_pos[0] + (self._target[0] - self._start_pos[0]) * ep
            sprite.y = self._start_pos[1] + (self._target[1] - self._start_pos[1]) * ep
            # 抛物线跳起：body_lift 按正弦弧线
            pose.body_lift = 35.0 * math.sin(p * math.pi)
            pose.body_stretch = math.sin(p * math.pi) * 0.8
            pose.leg_stride = 1.0
            pose.leg_phase += dt * 18.0
            if p >= 1.0:
                self._phase = "land"
                self._t = 0.0
                pose.body_lift = 0.0
                pose.body_stretch = 0.0
                pose.body_squash = 0.6  # 落地压扁
        elif self._phase == "land":
            p = clamp(self._t / self._land_time, 0.0, 1.0)
            pose.body_squash = 0.6 * (1.0 - ease_out_cubic(p))
            pose.tail_wag_phase += dt * 16.0
            if p >= 1.0:
                reset_to_stand(pose)
                self.finish()
