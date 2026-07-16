"""IDLE 状态：溜达 + 随机空闲小动作。

行为：
- 围绕"家"点（进入 IDLE 时的位置）在半径内随机游走（WalkAction）
- 游走间隙每隔一段时间随机播放一个空闲小动作（sit/groom/stretch）
- 鼠标移动（非甩脱）→ 转入 ChasingState
- 鼠标静止超 IDLE_SLEEP_AFTER_S → 转入 SleepingState
"""
from __future__ import annotations

import math
import random
import time

from cat import config
from cat.core.state_machine import State
from cat.models.cat.actions import IDLE_ACTIONS, make_action, weighted_choice
from cat.models.cat.states._intents import Intent, decide_intent
from cat.utils.geometry import clamp


def _in_play_cooldown(sprite) -> bool:
    """是否还在玩弄冷却期（刚玩腻走开，暂时不理鼠标）。"""
    return time.monotonic() < sprite.play_cooldown_until


class IdleState(State):
    name = "idle"

    def on_enter(self, sprite) -> None:
        # 记录"家"位置
        self._home_x = sprite.x
        self._home_y = sprite.y
        self._idle_timer = 0.0
        self._next_action_at = random.uniform(*config.IDLE_ACTION_INTERVAL_S)
        # 开始时先播放一个小站立姿态（清理上一状态残留动作）
        sprite.clear_action()
        sprite.pose.leg_stride = 0.0
        sprite.pose.tail_wag = 0.3

    def update(self, sprite, dt: float, mouse_state) -> None:
        ms = mouse_state

        # ---- 状态切换判定（用统一意图决策）----
        intent = decide_intent(sprite, ms)
        if intent == Intent.ALERT:
            sprite.fsm.transition_to("alert")
            return
        # 鼠标极近时直接进入玩弄（idle 也可能突然被凑脸）
        # 但玩腻冷却期内不进 playing（刚走开，让它真的离开一会儿）
        if intent == Intent.PLAY and not _in_play_cooldown(sprite):
            sprite.fsm.transition_to("playing")
            return
        if intent in (Intent.STALK, Intent.CHASE, Intent.POUNCE):
            # 鼠标已很近且有动作意图，先警觉再行动
            sprite.fsm.transition_to("alert")
            return
        # 长时间静止 → 睡
        if ms.still_seconds >= config.IDLE_SLEEP_AFTER_S:
            sprite.fsm.transition_to("sleeping")
            return

        # ---- 空闲行为调度 ----
        # 正在播放动作时不打断（让小动作完整播完）
        if sprite.has_action:
            return

        self._idle_timer += dt
        if self._idle_timer >= self._next_action_at:
            self._idle_timer = 0.0
            self._next_action_at = random.uniform(*config.IDLE_ACTION_INTERVAL_S)
            # 50% 概率游走，50% 概率做小动作
            if random.random() < 0.5:
                self._start_wander(sprite)
            else:
                self._start_idle_action(sprite)
            return

        # 没有动作且计时未到：偶尔看看四周（轻微头转）
        if not sprite.has_action:
            sprite.pose.head_turn = 0.3 * (
                1 if int(sprite.x * 0.1) % 2 == 0 else -1
            )
            sprite.pose.tail_wag_phase += dt * 1.5

    def _start_wander(self, sprite) -> None:
        """在"家"点附近随机选一个目标走过去。"""
        angle = random.uniform(0, math.tau)
        r = random.uniform(0, config.IDLE_WANDER_RADIUS_PX)
        tx = self._home_x + math.cos(angle) * r
        ty = self._home_y + math.sin(angle) * r
        # 限制在屏幕内（粗略，由 window 尺寸裁剪）
        tx = clamp(tx, 40, 4000)
        ty = clamp(ty, 40, 3000)
        sprite.play(make_action("walk", sprite=sprite, target=(tx, ty)))

    def _start_idle_action(self, sprite) -> None:
        """按权重选一个空闲小动作播放。groom 走独立状态。"""
        choice = weighted_choice(IDLE_ACTIONS, sprite.personality)
        family = choice["family"]
        if family == "groom":
            # groom 是独立状态（被打断逻辑不同）
            sprite.fsm.transition_to("grooming")
            return
        sprite.play(make_action(family, choice["variant"], sprite=sprite))
