"""CHASING 状态：追鼠标 + 扑击触发 + 甩脱判定。

进入时启动 RunAction（目标=鼠标当前位置，每帧动态求值）。
每帧检查：
- 甩脱（鼠标高速持续）→ IDLE
- 鼠标静止 → IDLE
- 进入扑击距离且概率命中 → POUNCING
"""
from __future__ import annotations

import math
import random

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import ACTIONS


class ChasingState(State):
    name = "chasing"

    def on_enter(self, sprite) -> None:
        # 目标用 callable：每帧取最新鼠标位置（由 sprite.mouse_state 提供）
        def mouse_pos():
            if sprite.mouse_state is not None:
                return sprite.mouse_state.pos
            return (sprite.x, sprite.y)

        sprite.clear_action()
        run = ACTIONS["run"](mouse_pos)
        sprite.play(run)
        # 标记：进入时短暂禁用扑击，避免一追上就扑（让追逐持续一会儿）
        self._chase_t = 0.0

    def update(self, sprite, dt: float, mouse_state) -> None:
        ms = mouse_state
        self._chase_t += dt

        # 甩脱 → 放弃
        if ms.is_escaping:
            sprite.clear_action()
            sprite.fsm.transition_to("idle")
            return
        # 鼠标静止 → 放弃
        if not ms.moving:
            sprite.clear_action()
            sprite.fsm.transition_to("idle")
            return

        # 扑击判定：追逐至少 0.2s 后，进入距离且有概率
        if self._chase_t > 0.2:
            dist = math.hypot(ms.pos[0] - sprite.x, ms.pos[1] - sprite.y)
            if dist < config.POUNCE_TRIGGER_DIST_PX:
                if random.random() < config.POUNCE_PROBABILITY:
                    sprite.clear_action()
                    sprite.fsm.transition_to("pouncing")
                    return
