"""POUNCING 状态：播放扑击动作。

进入时启动 PounceAction，目标=当前鼠标位置（锁定快照）。
动作结束后回到 IDLE。
"""
from __future__ import annotations

from cat.core.state_machine import State
from cat.models.cat.actions import ACTIONS


class PouncingState(State):
    name = "pouncing"

    def on_enter(self, sprite) -> None:
        # 锁定鼠标当前位置作为扑击目标
        target = sprite.mouse_state.pos if sprite.mouse_state else (sprite.x, sprite.y)
        sprite.clear_action()
        pounce = ACTIONS["pounce"](target)
        # 扑完后回 idle
        sprite.play(pounce, on_done=lambda: sprite.fsm.transition_to("idle"))

    def update(self, sprite, dt: float, mouse_state) -> None:
        # 扑击动作不可打断；on_done 会切回 idle。
        # 若动作因故未触发回调（例如被 clear），这里兜底切回 idle。
        if not sprite.has_action:
            sprite.fsm.transition_to("idle")
