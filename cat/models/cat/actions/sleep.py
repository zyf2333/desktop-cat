"""Sleep（睡觉）—— 持续状态动作。闭眼、身体蜷缩、冒 Z。

这个动作不会自然结束（duration=None），由 SleepingState 在鼠标移动时主动中止。
"""
from __future__ import annotations

from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand


class SleepAction(Action):
    name = "sleep"

    def __init__(self) -> None:
        super().__init__()
        self._t = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        pose = sprite.pose
        pose.asleep = True
        pose.body_squash = 0.55   # 蜷缩压扁
        pose.leg_stride = 0.0
        pose.tail_wag = 0.2
        pose.tail_angle = -0.6    # 尾巴蜷到身前
        pose.eye_open = 0.0

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        # 缓慢呼吸：身体极轻微起伏
        import math
        sprite.pose.body_squash = 0.5 + 0.05 * math.sin(self._t * 1.2)
        sprite.pose.tail_wag_phase += dt * 1.0
