"""Chase（追逐）—— 跟着鼠标跑，有玩耍感。

核心：速度不是恒定的，而是随机波动（忽快忽慢），偶尔停下来盯着鼠标再冲。
像真猫玩逗猫棒——追一阵、停一下、再扑。

不自行结束——由 ChasingState 在外部条件满足时切换（扑击/困惑/甩脱）。
"""
from __future__ import annotations

import math
import random

from cat import config
from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand
from cat.utils.geometry import move_towards


class ChaseAction(Action):
    name = "chase"

    def __init__(self, target) -> None:
        super().__init__()
        self._target = target
        self._done = False
        # 玩耍感状态
        self._speed_mult = 1.0       # 当前速度倍率（随机波动）
        self._speed_target = 1.0     # 目标倍率（缓动到这个值）
        self._speed_change_in = 0.0  # 距下次改变速度的倒计时
        self._pausing = False        # 是否在停顿
        self._pause_left = 0.0       # 停顿剩余时间

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        pose = sprite.pose
        pose.alerted = True
        pose.ear_alert = 0.8
        pose.pupil_dilate = 0.7
        pose.leg_stride = 1.0
        pose.tail_wag = 0.7
        pose.body_tilt = 0.15        # 奔跑前倾

    def update(self, sprite, dt: float) -> None:
        pose = sprite.pose
        target = self._target() if callable(self._target) else self._target

        # 朝向
        dx = target[0] - sprite.x
        dy = target[1] - sprite.y
        dist = math.hypot(dx, dy)
        if abs(dx) > 2:
            sprite.facing = 1 if dx > 0 else -1

        # ---- 玩耍感：速度波动 + 偶尔停顿 ----
        # 停顿逻辑
        if self._pausing:
            self._pause_left -= dt
            # 停顿时压低、盯着、尾巴兴奋抖
            pose.body_tilt = 0.0
            pose.body_squash = 0.3
            pose.tail_wag_phase += dt * 16.0
            if self._pause_left <= 0:
                self._pausing = False
                pose.body_squash = 0.0
                pose.body_tilt = 0.15
        else:
            # 随机触发停顿
            if random.random() < config.CHASE_PAUSE_PROBABILITY:
                self._pausing = True
                self._pause_left = random.uniform(*config.CHASE_PAUSE_DURATION_S)
            else:
                # 速度倍率缓动到目标，定期换目标（忽快忽慢）
                self._speed_change_in -= dt
                if self._speed_change_in <= 0:
                    self._speed_target = random.uniform(
                        1.0 - config.CHASE_SPEED_JITTER,
                        1.0 + config.CHASE_SPEED_JITTER,
                    )
                    self._speed_change_in = random.uniform(0.25, 0.7)

                # 缓动接近目标倍率
                self._speed_mult += (self._speed_target - self._speed_mult) * min(1.0, dt * 4.0)

                # 实际移动
                speed = config.CHASE_SPEED_PX_S * self._speed_mult
                # 距离很近时减速避免抖动
                if dist < config.CHASE_SLOWDOWN_DIST_PX:
                    speed *= max(0.1, dist / config.CHASE_SLOWDOWN_DIST_PX)
                new = move_towards((sprite.x, sprite.y), target, speed * dt)
                sprite.x, sprite.y = new

                pose.leg_phase += dt * (12.0 + 8.0 * self._speed_mult)
                pose.body_tilt = 0.15 * min(1.2, self._speed_mult)

        # 瞳孔追踪
        d = dist or 1.0
        pose.pupil_dx = (dx / d) * 0.85
        pose.pupil_dy = (dy / d) * 0.65
