"""Walk（走）——以低速向目标点移动。

模板动作：演示位移类动作如何更新位置、朝向、姿态相位。
"""
from __future__ import annotations

import math

from cat import config
from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand
from cat.utils.geometry import direction, move_towards


class WalkAction(Action):
    name = "walk"

    def __init__(self, target, speed_px_s: float = config.IDLE_WANDER_SPEED_PX_S) -> None:
        super().__init__()
        # target 可以是 (x,y) 或返回 (x,y) 的 callable（每帧动态求值）
        self._target = target
        self._speed = speed_px_s
        self._arrived = False

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        sprite.pose.leg_stride = 0.6
        sprite.pose.tail_wag = 0.4

    def update(self, sprite, dt: float) -> None:
        target = self._target() if callable(self._target) else self._target
        # 朝向
        dx = target[0] - sprite.x
        if abs(dx) > 2:
            sprite.facing = 1 if dx > 0 else -1

        # 移动
        new_pos = move_towards((sprite.x, sprite.y), target, self._speed * dt)
        sprite.x, sprite.y = new_pos

        # 腿摆相位（步频随速度）
        sprite.pose.leg_phase += dt * 9.0

        # 瞳孔看向行进方向
        d = direction((sprite.x, sprite.y), target)
        sprite.pose.pupil_dx = d[0] * 0.6
        sprite.pose.pupil_dy = d[1] * 0.4

        # 到达判定
        if math.hypot(target[0] - sprite.x, target[1] - sprite.y) < 3:
            self._arrived = True
            self.finish()

    def is_done(self) -> bool:
        return self._arrived or super().is_done()
