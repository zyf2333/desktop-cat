"""Run（跑）——以较高速度追踪一个动态目标（鼠标）。

与 Walk 的区别：速度更快、腿摆更激烈、身体微前倾。
目标通常是鼠标当前位置（callable 形式，每帧求值）。
"""
from __future__ import annotations

import math

from cat import config
from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand
from cat.utils.geometry import direction, move_towards


class RunAction(Action):
    name = "run"

    def __init__(self, target, speed_px_s: float = config.CHASE_SPEED_PX_S) -> None:
        super().__init__()
        self._target = target
        self._speed = speed_px_s
        self._done = False

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        sprite.pose.leg_stride = 1.0
        sprite.pose.tail_wag = 0.7
        sprite.pose.body_tilt = 0.18  # 前倾

    def update(self, sprite, dt: float) -> None:
        target = self._target() if callable(self._target) else self._target

        dx = target[0] - sprite.x
        if abs(dx) > 2:
            sprite.facing = 1 if dx > 0 else -1

        # 接近目标时减速，避免在目标点抖动
        dist = math.hypot(dx, target[1] - sprite.y)
        speed = self._speed
        if dist < config.CHASE_SLOWDOWN_DIST_PX:
            speed *= dist / config.CHASE_SLOWDOWN_DIST_PX

        new_pos = move_towards((sprite.x, sprite.y), target, speed * dt)
        sprite.x, sprite.y = new_pos

        sprite.pose.leg_phase += dt * 16.0  # 跑步快摆

        d = direction((sprite.x, sprite.y), target)
        sprite.pose.pupil_dx = d[0] * 0.8
        sprite.pose.pupil_dy = d[1] * 0.6

        # RunAction 不会自行结束；由 ChasingState 在外部条件满足时中止
        # （扑击触发或甩脱判定后，State 会 clear_action）

    def is_done(self) -> bool:
        return self._done
