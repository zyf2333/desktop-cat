"""STALKING 状态：压低身体缓慢接近猎物。

- 进入玩距（且概率命中）→ PLAYING（玩弄）
- 进入扑击距离 → POUNCING（蓄力→冲刺）
- 潜行超时 → CHASING（改追逐）
- 鼠标变快 → CHASING
- 鼠标丢失 → CONFUSED
"""
from __future__ import annotations

import random

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import make_action
from cat.models.cat.states._conditions import dist_to_mouse, lost_mouse, mouse_pos


class StalkingState(State):
    name = "stalking"

    def on_enter(self, sprite) -> None:
        sprite.clear_action()
        sprite.play(make_action("stalk", sprite=sprite, target=lambda: mouse_pos(sprite)))
        self._stalk_t = 0.0

    def update(self, sprite, dt: float, mouse_state) -> None:
        self._stalk_t += dt

        if lost_mouse(sprite, mouse_state):
            sprite.clear_action()
            sprite.fsm.transition_to("confused")
            return

        d = dist_to_mouse(sprite, mouse_state)
        speed = mouse_state.speed_smooth if mouse_state else 0.0

        # 进入玩距 → 概率进入玩弄
        if d <= config.PLAY_DIST_PX:
            if random.random() < config.STALK_TO_PLAY_PROB:
                sprite.clear_action()
                sprite.fsm.transition_to("playing")
                return
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
        # 鼠标突然变快 → 改追逐（慢目标才适合潜行）
        if speed > config.STALK_MOUSE_SPEED_PX_S * 1.5:
            sprite.clear_action()
            sprite.fsm.transition_to("chasing")
            return
