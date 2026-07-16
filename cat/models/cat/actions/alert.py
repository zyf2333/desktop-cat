"""Alert（警觉）—— 猫发现鼠标进入警戒范围的第一反应。

姿态：耳朵竖起、瞳孔放大追踪鼠标、身体微紧、尾巴停止摆动。
持续一段随机时间后自然结束（由 State 决定下一步：发现）。
"""
from __future__ import annotations

import math
import random

from cat import config
from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand


class AlertAction(Action):
    name = "alert"

    def __init__(self, duration: float | None = None) -> None:
        super().__init__()
        self._duration = duration if duration is not None else random.uniform(*config.ALERT_DURATION_S)
        self._t = 0.0

    def start(self, sprite) -> None:
        super().start(sprite)
        reset_to_stand(sprite.pose)
        pose = sprite.pose
        pose.alerted = True
        pose.ear_alert = 1.0       # 竖耳
        pose.pupil_dilate = 0.6    # 瞳孔放大
        pose.tail_wag = 0.0        # 警觉时尾巴不动
        pose.leg_stride = 0.0

    def update(self, sprite, dt: float) -> None:
        self._t += dt
        pose = sprite.pose
        # 瞳孔死盯鼠标方向
        if sprite.mouse_state is not None:
            dx = sprite.mouse_state.pos[0] - sprite.x
            dy = sprite.mouse_state.pos[1] - sprite.y
            d = math.hypot(dx, dy) or 1.0
            pose.pupil_dx = (dx / d) * 0.9
            pose.pupil_dy = (dy / d) * 0.7
            # 头也微微转向鼠标
            pose.head_turn = max(-1.0, min(1.0, dx / 200.0))
        # 耳朵极轻微颤动（紧张感）
        pose.ear_alert = 0.9 + 0.1 * math.sin(self._t * 18.0)
        if self._t >= self._duration:
            self.finish()
