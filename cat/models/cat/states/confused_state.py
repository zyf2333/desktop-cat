"""CONFUSED 状态：找不到鼠标，四处张望，然后回 IDLE。

播放 ConfusedAction。动作结束 → IDLE（继续干自己的事）。
若困惑期间鼠标又回到警觉范围 → 重新 ALERT（又发现了）。
"""
from __future__ import annotations

from cat.core.state_machine import State
from cat.models.cat.actions import ACTIONS
from cat.models.cat.states._conditions import in_alert_range


class ConfusedState(State):
    name = "confused"

    def on_enter(self, sprite) -> None:
        sprite.clear_action()
        sprite.play(
            ACTIONS["confused"](),
            on_done=lambda: sprite.fsm.transition_to("idle"),
        )

    def update(self, sprite, dt: float, mouse_state) -> None:
        # 困惑中鼠标又靠近且在动 → 重新警觉
        if in_alert_range(sprite, mouse_state):
            sprite.clear_action()
            sprite.fsm.transition_to("alert")
            return
        # 动作自然结束的兜底
        if not sprite.has_action:
            sprite.fsm.transition_to("idle")
