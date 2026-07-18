"""Swat（爪拍）—— PLAYING 状态动作：用爪子快速拍打鼠标位置。

在鼠标旁边，身体压低，单爪快速抬起拍下，重复几次。
像猫玩逗猫棒/虫子的标志性动作。
"""
from __future__ import annotations

import math
import random

from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand


class SwatAction(Action):
    name = "swat"

    def __init__(self, target, swats: int | None = None) -> None:
        super().__init__()
        self._target = target
        # 拍几下（受个性玩心影响，在 start 里最终确定）
        self._swats_total = swats
        self._t = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        n = self._swats_total
        if n is None:
            # 玩心高的猫拍更多下
            n = random.randint(2, 3 + int(sprite.personality.playfulness * 3))
        self._swats_total = n
        self._swat_period = 0.65  # 放慢：抬爪、停住抓取、再收回
        self._total_time = self._swat_period * self._swats_total + 0.2
        pose = sprite.pose
        pose.alerted = True
        pose.ear_alert = 0.8
        pose.pupil_dilate = 0.8
        pose.body_squash = 0.35  # 压低准备
        pose.mouth = "open"

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        pose = sprite.pose
        target = self._target() if callable(self._target) else self._target

        # 朝向目标
        dx = target[0] - sprite.x
        if abs(dx) > 2:
            sprite.facing = 1 if dx > 0 else -1

        # 爪子拍打：慢抬 → 顶部停住观察/抓取 → 慢收回。
        phase = (self._t % self._swat_period) / self._swat_period
        if phase < 0.32:
            local = phase / 0.32
            pose.paw_raise = math.sin(local * math.pi / 2)
        elif phase < 0.62:
            pose.paw_raise = 1.0
        else:
            local = (phase - 0.62) / 0.38
            pose.paw_raise = math.cos(local * math.pi / 2)
        # 收爪时身体只有很轻的回弹，不再快速震动。
        if phase > 0.62:
            pose.body_squash = 0.35 + 0.035 * math.sin(phase * math.pi * 2)
        # 耳朵兴奋颤动
        pose.ear_alert = 0.75 + 0.08 * math.sin(self._t * 10)
        pose.tail_wag_phase += dt * 7.0

        if self._t >= self._total_time:
            reset_to_stand(pose)
            self.finish()
