"""STALKING 状态：压低身体缓慢接近猎物。

- 距离进入扑击准备范围 → POUNCING（蓄力→冲刺）
- 潜行超时（猎物一直保持距离）→ CHASING（改用追逐）
- 鼠标丢失 → CONFUSED
"""
from __future__ import annotations

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import ACTIONS
from cat.models.cat.states._conditions import dist_to_mouse, lost_mouse, mouse_pos


class StalkingState(State):
    name = "stalking"

    def on_enter(self, sprite) -> None:
        sprite.clear_action()
        sprite.play(ACTIONS["stalk"](lambda: mouse_pos(sprite)))
        self._stalk_t = 0.0

    def update(self, sprite, dt: float, mouse_state) -> None:
        self._stalk_t += dt

        if lost_mouse(sprite, mouse_state):
            sprite.clear_action()
            sprite.fsm.transition_to("confused")
            return

        d = dist_to_mouse(sprite, mouse_state)
        # 够近了 → 准备扑击
        if d <= config.STALK_END_DIST_PX:
            sprite.clear_action()
            sprite.fsm.transition_to("pouncing")
            return
        # 潜行太久还靠近不了 → 改追逐
        if self._stalk_t >= config.STALK_GIVEUP_S:
            sprite.clear_action()
            sprite.fsm.transition_to("chasing")
            return
