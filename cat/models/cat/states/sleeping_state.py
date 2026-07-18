"""SLEEPING 状态：睡觉，直到鼠标移动。

播放 SleepAction（持续不结束）。鼠标有任何移动 → 醒来回 IDLE。
"""
from __future__ import annotations

import random

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import make_action
from cat.models.cat.states._conditions import dist_to_mouse


class SleepingState(State):
    name = "sleeping"

    def on_enter(self, sprite) -> None:
        sprite.clear_action()
        sprite.awake_seconds = 0.0
        sprite.sleep_after_seconds = random.uniform(*config.AUTONOMOUS_SLEEP_AFTER_S)
        sprite.play(make_action("sleep", sprite=sprite))

    def update(self, sprite, dt: float, mouse_state) -> None:
        # 只有鼠标靠近或直接碰到猫才会惊醒；远处用户工作不再反复吵醒它。
        nearby = dist_to_mouse(sprite, mouse_state) <= config.ALERT_RADIUS_PX
        if sprite.is_hovered or (mouse_state.moving and nearby):
            sprite.clear_action()
            sprite.fsm.transition_to("alert")
