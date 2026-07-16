"""Pounce（扑击）—— 两阶段动作：蓄力 → 冲刺。

蓄力：压低身体（body_squash 升高），瞳孔放大盯住目标。
冲刺：朝冲刺目标高速移动，带轻微跳起（body_lift），收尾有过冲回弹。

扑击目标在 start 时锁定（冲刺到鼠标"那一刻"的位置），
这是真猫的行为：扑向预判点，而不是一直追着鼠标。
"""
from __future__ import annotations

import math

from cat import config
from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand
from cat.utils.geometry import clamp, direction, ease_out_back, ease_out_cubic, move_towards


class PounceAction(Action):
    name = "pounce"

    PHASE_WINDUP = "windup"
    PHASE_LUNGE = "lunge"
    PHASE_RECOVER = "recover"

    def __init__(self, target) -> None:
        super().__init__()
        # target 可以是 (x,y) 或 callable；start 时锁定为快照
        self._target_fn = target
        self._target = (0.0, 0.0)

        self._phase = self.PHASE_WINDUP
        self._t = 0.0  # 当前阶段累计时间

        # 冲刺起止点与进度
        self._lunge_start = (0.0, 0.0)
        self._lunge_dist = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        # 锁定冲刺目标
        self._target = self._target_fn() if callable(self._target_fn) else self._target_fn
        self._lunge_start = (sprite.x, sprite.y)
        # 限制冲刺最大距离
        d = math.hypot(self._target[0] - sprite.x, self._target[1] - sprite.y)
        if d > config.POUNCE_MAX_DIST_PX:
            ux = (self._target[0] - sprite.x) / d
            uy = (self._target[1] - sprite.y) / d
            self._target = (
                sprite.x + ux * config.POUNCE_MAX_DIST_PX,
                sprite.y + uy * config.POUNCE_MAX_DIST_PX,
            )
        self._lunge_dist = math.hypot(
            self._target[0] - self._lunge_start[0],
            self._target[1] - self._lunge_start[1],
        )
        # 朝向锁定目标方向
        if self._target[0] >= sprite.x:
            sprite.facing = 1
        else:
            sprite.facing = -1
        self._enter_windup(sprite)

    # ---- 阶段切换 ----
    def _enter_windup(self, sprite) -> None:
        self._phase = self.PHASE_WINDUP
        self._t = 0.0
        pose = sprite.pose
        reset_to_stand(pose)
        pose.leg_stride = 0.0
        pose.tail_wag = 0.9
        pose.tail_angle = -0.3  # 尾巴压低抖动
        pose.pupil_dx = sprite.facing * 0.8  # 死盯目标
        pose.pupil_dy = 0.2

    def _enter_lunge(self, sprite) -> None:
        self._phase = self.PHASE_LUNGE
        self._t = 0.0
        pose = sprite.pose
        pose.body_squash = 0.0
        pose.body_stretch = 1.0  # 拉长身体
        pose.body_lift = 14.0    # 跳起
        pose.leg_stride = 1.0

    def _enter_recover(self, sprite) -> None:
        self._phase = self.PHASE_RECOVER
        self._t = 0.0
        pose = sprite.pose
        pose.body_stretch = 0.0
        pose.body_lift = 0.0
        pose.body_squash = 0.5  # 落地压扁

    # ---- 每帧 ----
    def update(self, sprite, dt: float) -> None:
        self._t += dt

        if self._phase == self.PHASE_WINDUP:
            p = clamp(self._t / config.POUNCE_WINDUP_S, 0.0, 1.0)
            sprite.pose.body_squash = p  # 渐渐压低
            sprite.pose.tail_wag_phase += dt * 20.0  # 尾巴兴奋抖动
            if self._t >= config.POUNCE_WINDUP_S:
                self._enter_lunge(sprite)

        elif self._phase == self.PHASE_LUNGE:
            # 冲刺持续时间按距离/速度估算
            lunge_time = max(0.05, self._lunge_dist / config.POUNCE_SPEED_PX_S)
            p = clamp(self._t / lunge_time, 0.0, 1.0)
            ep = ease_out_cubic(p)
            sprite.x = self._lunge_start[0] + (self._target[0] - self._lunge_start[0]) * ep
            sprite.y = self._lunge_start[1] + (self._target[1] - self._lunge_start[1]) * ep
            sprite.pose.leg_phase += dt * 22.0
            if p >= 1.0:
                sprite.x, sprite.y = self._target
                self._enter_recover(sprite)

        elif self._phase == self.PHASE_RECOVER:
            p = clamp(self._t / 0.18, 0.0, 1.0)
            ep = ease_out_back(p)
            sprite.pose.body_squash = 0.5 * (1.0 - ep)
            if self._t >= 0.18:
                reset_to_stand(sprite.pose)
                self.finish()
