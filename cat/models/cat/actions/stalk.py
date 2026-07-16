"""Stalk（潜行）—— 压低身体、缓慢接近猎物。

这是真猫捕猎的标志动作：身体压得很低、步伐很小很慢、眼睛死盯目标。
不自行结束——由 StalkingState 在距离够近时切换到扑击蓄力，
或潜行超时还没靠近则转追逐。
"""
from __future__ import annotations

import math

from cat import config
from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand
from cat.utils.geometry import move_towards


class StalkAction(Action):
    name = "stalk"

    def __init__(self, target) -> None:
        super().__init__()
        self._target = target  # callable 返回当前鼠标位置
        self._done = False
        self._speed_mult = 1.0

    def start(self, sprite) -> None:
        super().start(sprite)
        # 个性影响潜行速度：有耐心的猫潜行更慢更稳（patience 0→1.3x，1→0.7x）
        self._speed_mult = 1.3 - 0.6 * sprite.personality.patience
        reset_to_stand(sprite.pose)
        pose = sprite.pose
        pose.alerted = True
        pose.ear_alert = 1.0
        pose.pupil_dilate = 1.0
        pose.body_squash = 0.55      # 压得很低
        pose.leg_stride = 0.25       # 小碎步
        pose.tail_wag = 0.3
        pose.tail_angle = -0.2       # 尾巴压低

    def update(self, sprite, dt: float) -> None:
        pose = sprite.pose
        target = self._target() if callable(self._target) else self._target

        # 朝向
        dx = target[0] - sprite.x
        if abs(dx) > 2:
            sprite.facing = 1 if dx > 0 else -1

        # 缓慢接近（个性 patience 影响速度）
        new = move_towards((sprite.x, sprite.y), target, config.STALK_SPEED_PX_S * self._speed_mult * dt)
        sprite.x, sprite.y = new

        # 瞳孔死盯
        dy = target[1] - sprite.y
        d = math.hypot(dx, dy) or 1.0
        pose.pupil_dx = (dx / d) * 0.95
        pose.pupil_dy = (dy / d) * 0.8

        # 小碎步相位
        pose.leg_phase += dt * 5.0
        # 尾巴尖抖
        pose.tail_wag_phase += dt * 8.0
        # 身体压低时偶尔轻微起伏（匍匐前进的节奏）
        pose.body_squash = 0.5 + 0.08 * math.sin(pose.leg_phase)
