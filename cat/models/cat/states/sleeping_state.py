"""SLEEPING 状态：睡觉，直到鼠标移动。

播放 SleepAction（持续不结束）。鼠标有任何移动 → 醒来回 IDLE。
"""
from __future__ import annotations

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import make_action


class SleepingState(State):
    name = "sleeping"

    def on_enter(self, sprite) -> None:
        sprite.clear_action()
        sprite.play(make_action("sleep", sprite=sprite))

    def update(self, sprite, dt: float, mouse_state) -> None:
        # 鼠标有任何移动 → 醒来
        if mouse_state.moving:
            sprite.clear_action()
            sprite.fsm.transition_to("idle")
