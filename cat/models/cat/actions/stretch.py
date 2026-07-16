"""Stretch（伸懒腰）—— 空闲小动作。身体拉长、前腿前伸、弓背。"""
from __future__ import annotations

from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand
from cat.utils.geometry import ease_in_out_cubic


class StretchAction(Action):
    name = "stretch"

    def __init__(self, duration: float = 1.4) -> None:
        super().__init__()
        self._duration = duration
        self._t = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        sprite.pose.leg_stride = 0.0

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        p = self._t / self._duration
        if p >= 1.0:
            reset_to_stand(sprite.pose)
            self.finish()
            return
        # 0→0.4 拉伸渐强，0.4→1.0 回落
        if p < 0.4:
            k = ease_in_out_cubic(p / 0.4)
        else:
            k = 1.0 - ease_in_out_cubic((p - 0.4) / 0.6)
        sprite.pose.body_stretch = k * 0.8
        sprite.pose.body_tilt = -k * 0.15  # 略后仰
        sprite.pose.leg_stride = k * 0.5
        sprite.pose.tail_wag = 0.5
        sprite.pose.tail_wag_phase += dt * 4.0
        sprite.pose.eye_open = 0.6  # 舒服得眯眼
