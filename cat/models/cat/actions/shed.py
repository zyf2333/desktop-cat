"""Shed（掉毛）—— 空闲小动作：猫抖动身体，掉下几缕毛絮。

猫快速小幅度抖动（像甩掉身上的浮毛），同时生成毛絮粒子从身上飘落。
毛絮粒子用代码绘制（白色小椭圆 + 重力下落 + 随机漂移），不依赖素材。

粒子状态存在 sprite 上（pose 不适合存动态列表），由 catsprite model 读取绘制。
"""
from __future__ import annotations

import math
import random

from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand


class FurParticle:
    """一缕飘落的毛絮。"""

    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "rot", "rot_v")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        # 初速度：小幅随机抛出
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(-5, 5)
        self.max_life = random.uniform(1.5, 2.8)
        self.life = self.max_life
        self.size = random.uniform(2.0, 3.5)
        self.rot = random.uniform(0, math.tau)
        self.rot_v = random.uniform(-3, 3)


class ShedAction(Action):
    name = "shed"

    def __init__(self, duration: float | None = None) -> None:
        super().__init__()
        self._duration = duration
        self._t = 0.0
        self._shed_accum = 0.0  # 掉毛累积计时

    def start(self, sprite) -> None:
        super().start(sprite)
        d = self._duration
        if d is None:
            d = random.uniform(1.2, 2.2)
        self._duration = d
        reset_to_stand(sprite.pose)
        # 初始化粒子列表挂在 sprite 上（catsprite model 会读取绘制）
        if not hasattr(sprite, "fur_particles") or sprite.fur_particles is None:
            sprite.fur_particles = []
        pose = sprite.pose
        pose.tail_wag = 0.4
        pose.leg_stride = 0.0

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        pose = sprite.pose
        # 抖动：身体快速小幅震荡（用高频 sin）
        shake = math.sin(self._t * 28.0) * 0.08
        pose.body_tilt = shake
        pose.head_turn = math.sin(self._t * 24.0) * 0.15
        pose.tail_wag_phase += dt * 10.0

        # 掉毛：每隔一段时间生成一缕（粒子推进由 PetSprite 统一处理）
        self._shed_accum += dt
        shed_interval = 0.18  # 每 0.18s 掉一缕
        while self._shed_accum >= shed_interval:
            self._shed_accum -= shed_interval
            self._spawn_fur(sprite)

        if self._t >= self._duration:
            reset_to_stand(pose)
            self.finish()

    def _spawn_fur(self, sprite) -> None:
        """从猫身上随机位置掉一缕毛（坐标相对猫中心，便于 model 绘制）。"""
        # 相对猫中心的偏移（猫中心是 painter 已 translate 到的点）
        r = sprite.size_px * 0.35
        px = random.uniform(-r, r)
        py = random.uniform(-r * 0.6, r * 0.3)
        sprite.fur_particles.append(FurParticle(px, py))
