"""ALERT 状态：猫发现鼠标进入警戒范围的第一反应。

播放 AlertAction（竖耳、瞳孔追踪）。动作结束后转入 NOTICE。
若动作期间鼠标已离开关注范围 → 直接 CONFUSED。
"""
from __future__ import annotations

from cat.core.state_machine import State
from cat.models.cat.actions import make_action
from cat.models.cat.states._conditions import lost_mouse


class AlertState(State):
    name = "alert"

    def on_enter(self, sprite) -> None:
        sprite.clear_action()
        sprite.play(
            make_action("alert", sprite=sprite),
            on_done=lambda: sprite.fsm.transition_to("noticed"),
        )

    def update(self, sprite, dt: float, mouse_state) -> None:
        # 鼠标已经跑出关注范围 → 困惑
        if lost_mouse(sprite, mouse_state):
            sprite.clear_action()
            sprite.fsm.transition_to("confused")
            return
        # 动作未自然结束时的兜底（极端情况）
        if not sprite.has_action:
            sprite.fsm.transition_to("noticed")
