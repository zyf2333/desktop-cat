"""Poop（排便）——偶尔蹲下，完成后在桌面留下便便。"""
from __future__ import annotations

import math
import random

from cat import config
from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand


class Dropping:
    __slots__ = ("x", "y", "size")

    def __init__(self, x: float, y: float, size: float) -> None:
        self.x = x
        self.y = y
        self.size = size


class PoopAction(Action):
    name = "poop"

    def __init__(self, duration: float | None = None) -> None:
        super().__init__()
        self._duration = duration
        self._t = 0.0
        self._spawned = False

    def start(self, sprite) -> None:
        super().start(sprite)
        if self._duration is None:
            self._duration = random.uniform(*config.POOP_DURATION_S)
        reset_to_stand(sprite.pose)
        sprite.pose.body_squash = 0.3
        sprite.pose.tail_angle = 0.9
        sprite.pose.tail_wag = 0.15
        if not hasattr(sprite, "droppings"):
            sprite.droppings = []

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        # 轻微用力起伏，不再旋转整只猫。
        sprite.pose.body_squash = 0.28 + 0.05 * math.sin(self._t * 7.0)
        sprite.pose.head_bob = 1.5 * math.sin(self._t * 5.0)
        if self._t >= self._duration:
            if not self._spawned:
                self._spawn(sprite)
            reset_to_stand(sprite.pose)
            self.finish()

    def _spawn(self, sprite) -> None:
        self._spawned = True
        size_px = float(getattr(sprite, "size_px", 96))
        # 留在猫身后、脚边；世界坐标独立于猫，猫走后仍留在原处。
        # 像素猫排便时使用正面 idle 帧，尾巴固定画在右侧；矢量猫才按 facing 翻转。
        if getattr(getattr(sprite, "model", None), "name", None) == "catsprite":
            x = sprite.x + size_px * 0.62
        else:
            x = sprite.x - sprite.facing * size_px * 0.62
        y = sprite.y + size_px * 0.27
        sprite.droppings.append(Dropping(x, y, max(5.0, size_px * 0.085)))
