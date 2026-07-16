"""GROOMING 状态：舔毛（独立状态）。

播放 GroomAction。结束后回 IDLE。
若舔毛过程中鼠标开始移动，也提前结束回 IDLE（猫被打断）。
"""
from __future__ import annotations

from cat.core.state_machine import State
from cat.models.cat.actions import ACTIONS


class GroomingState(State):
    name = "grooming"

    def on_enter(self, sprite) -> None:
        sprite.clear_action()
        sprite.play(
            ACTIONS["groom"](),
            on_done=lambda: sprite.fsm.transition_to("idle"),
        )

    def update(self, sprite, dt: float, mouse_state) -> None:
        # 舔毛被打断：鼠标移动则停止
        if mouse_state.moving:
            sprite.clear_action()
            sprite.fsm.transition_to("idle")
            return
        # 动作自然结束的兜底
        if not sprite.has_action:
            sprite.fsm.transition_to("idle")
