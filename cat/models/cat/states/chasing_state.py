"""CHASING 状态：带玩耍感的追逐（速度波动+停顿）。

- 进入玩距且概率命中 → PLAYING（玩弄）
- 进入扑击距离且概率命中 → POUNCING
- 鼠标丢失 → CONFUSED
- 鼠标静止 → IDLE
"""
from __future__ import annotations

import math
import random

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import make_action
from cat.models.cat.states._conditions import dist_to_mouse, lost_mouse, mouse_pos


class ChasingState(State):
    name = "chasing"

    def on_enter(self, sprite) -> None:
        sprite.clear_action()
        sprite.play(make_action("chase", sprite=sprite, target=lambda: mouse_pos(sprite)))
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

        if self._chase_t > 0.3:
            d = dist_to_mouse(sprite, mouse_state)
            # 进入玩距 → 玩弄（逗猫棒玩法）
            if d <= config.PLAY_DIST_PX:
                if random.random() < config.CHASE_TO_PLAY_PROB:
                    sprite.clear_action()
                    sprite.fsm.transition_to("playing")
                    return
            # 进入扑击距离 → 扑击
            if d < config.CHASE_TO_POUNCE_DIST_PX:
                if random.random() < config.CHASE_TO_POUNCE_PROB:
                    sprite.clear_action()
                    sprite.fsm.transition_to("pouncing")
                    return
