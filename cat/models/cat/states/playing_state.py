"""PLAYING 状态：在鼠标旁边像逗猫棒一样玩。

进入后随机轮换 play 族变体（swat/jump_pounce/wrestle/sniff）。
每个动作完成后，根据个性和鼠标状态决定：
- 继续玩（选下一个 play 变体）
- 鼠标跑了 → chasing（继续追）
- 鼠标丢失 → confused
- 玩腻了（超时或玩心低）→ idle

这是"逗猫棒玩法"的核心：猫凑在鼠标旁边反复拍、跳、扭、嗅。
"""
from __future__ import annotations

import random

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import make_action
from cat.models.cat.states._conditions import dist_to_mouse, lost_mouse, mouse_pos


class PlayingState(State):
    name = "playing"

    def on_enter(self, sprite) -> None:
        self._play_t = 0.0
        self._play_count = 0
        # 玩心决定最多玩几轮（玩心 0→2轮，1→7轮）
        p = sprite.personality
        self._max_rounds = random.randint(2, 3 + int(p.playfulness * 5))
        self._start_play(sprite)

    def _start_play(self, sprite) -> None:
        """选一个 play 变体播放。target 用 callable 跟踪鼠标。"""
        sprite.clear_action()
        # swat/sniff/jump_pounce 需要跟踪鼠标；wrestle 不需要
        target = lambda: mouse_pos(sprite)
        action = make_action("play", sprite=sprite, target=target)
        sprite.play(action, on_done=lambda: self._after_play(sprite))

    def update(self, sprite, dt: float, mouse_state) -> None:
        self._play_t += dt

        # 鼠标丢失 → 困惑
        if lost_mouse(sprite, mouse_state):
            sprite.clear_action()
            sprite.fsm.transition_to("confused")
            return

        # 鼠标快速逃开（还在视野但变远且快）→ 追
        d = dist_to_mouse(sprite, mouse_state)
        if mouse_state is not None and d > config.PLAY_DIST_PX * 2.5 and mouse_state.moving:
            sprite.clear_action()
            sprite.fsm.transition_to("chasing")
            return

        # 动作自然结束的兜底（on_done 应已处理）
        if not sprite.has_action:
            self._after_play(sprite)

    def _after_play(self, sprite) -> None:
        """一个 play 动作完成后：决定继续玩还是退出。"""
        self._play_count += 1
        ms = sprite.mouse_state

        # 玩够轮数 → 回 idle（玩腻了）
        if self._play_count >= self._max_rounds:
            sprite.fsm.transition_to("idle")
            return

        # 鼠标丢失 → 困惑
        if ms is None or lost_mouse(sprite, ms):
            sprite.fsm.transition_to("confused")
            return

        # 否则继续玩下一个变体
        self._start_play(sprite)
