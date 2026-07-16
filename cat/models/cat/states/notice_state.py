"""NOTICED 状态：确认是猎物，压低姿态，准备行动。

播放 NoticeAction。结束后根据距离决定：近则潜行（STALKING），远则直接追（CHASING）。
"""
from __future__ import annotations

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import ACTIONS
from cat.models.cat.states._conditions import dist_to_mouse, lost_mouse


class NoticeState(State):
    name = "noticed"

    def on_enter(self, sprite) -> None:
        sprite.clear_action()
        sprite.play(ACTIONS["notice"]())

    def update(self, sprite, dt: float, mouse_state) -> None:
        if lost_mouse(sprite, mouse_state):
            sprite.clear_action()
            sprite.fsm.transition_to("confused")
            return
        # 动作自然结束 → 按距离分流
        if not sprite.has_action:
            d = dist_to_mouse(sprite, mouse_state)
            if d <= config.STALK_END_DIST_PX * 2.5:
                # 已经很近，直接准备扑击
                sprite.fsm.transition_to("stalking")
            else:
                # 较远，先潜行或直接追（这里统一进潜行，潜行超时会转追）
                sprite.fsm.transition_to("stalking")
