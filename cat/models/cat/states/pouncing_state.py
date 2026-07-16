"""POUNCING 状态：播放扑击动作（蓄力→冲刺→收尾）。

进入时启动 PounceAction，目标=当前鼠标位置（锁定快照）。
动作结束后：鼠标还在附近且在动 → 继续追逐（玩耍）；否则 → IDLE。
"""
from __future__ import annotations

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import ACTIONS
from cat.models.cat.states._conditions import dist_to_mouse, lost_mouse


class PouncingState(State):
    name = "pouncing"

    def on_enter(self, sprite) -> None:
        # 锁定鼠标当前位置作为扑击目标
        target = sprite.mouse_state.pos if sprite.mouse_state else (sprite.x, sprite.y)
        sprite.clear_action()
        pounce = ACTIONS["pounce"](target)
        sprite.play(pounce, on_done=lambda: self._after_pounce(sprite))

    def update(self, sprite, dt: float, mouse_state) -> None:
        # 扑击动作不可打断；on_done 会处理后续切换。
        # 兜底：动作因故未触发回调时切走。
        if not sprite.has_action:
            self._after_pounce(sprite)

    def _after_pounce(self, sprite) -> None:
        """扑击完成后：鼠标还在附近且在动 → 继续追；否则回 idle。"""
        ms = sprite.mouse_state
        if ms is not None and ms.moving and not lost_mouse(sprite, ms):
            # 还在玩，继续追逐
            sprite.fsm.transition_to("chasing")
        else:
            sprite.fsm.transition_to("idle")
