"""CHASING 状态：带玩耍感的追逐（速度波动+停顿）。

- 进入扑击距离且概率命中 → POUNCING
- 鼠标丢失（超出范围或甩脱）→ CONFUSED
- 鼠标静止（玩累了？）→ IDLE
"""
from __future__ import annotations

import math
import random

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import ACTIONS
from cat.models.cat.states._conditions import dist_to_mouse, lost_mouse, mouse_pos


class ChasingState(State):
    name = "chasing"

    def on_enter(self, sprite) -> None:
        sprite.clear_action()
        sprite.play(ACTIONS["chase"](lambda: mouse_pos(sprite)))
        self._chase_t = 0.0

    def update(self, sprite, dt: float, mouse_state) -> None:
        self._chase_t += dt

        # 鼠标丢失 → 困惑
        if lost_mouse(sprite, mouse_state):
            sprite.clear_action()
            sprite.fsm.transition_to("confused")
            return
        # 鼠标静止 → 放弃回 idle
        if not mouse_state.moving:
            sprite.clear_action()
            sprite.fsm.transition_to("idle")
            return

        # 扑击判定：追了一会儿后，进入距离且有概率
        if self._chase_t > 0.3:
            d = dist_to_mouse(sprite, mouse_state)
            if d < config.CHASE_TO_POUNCE_DIST_PX:
                if random.random() < config.CHASE_TO_POUNCE_PROB:
                    sprite.clear_action()
                    sprite.fsm.transition_to("pouncing")
                    return
