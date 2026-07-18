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
from cat.models.cat.states._conditions import dist_to_mouse
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
        self._next_action_at = self._next_interval(sprite)
        self._zoomies_remaining = 0
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
        mouse_far = dist_to_mouse(sprite, ms) > config.ALERT_RADIUS_PX
        # 鼠标长时间静止，或者猫在远处活动够久后自然犯困。
        if (ms.still_seconds >= config.IDLE_SLEEP_AFTER_S or
                (mouse_far and sprite.awake_seconds >= sprite.sleep_after_seconds)):
            sprite.fsm.transition_to("sleeping")
            return

        # ---- 空闲行为调度 ----
        # 正在播放动作时不打断（让小动作完整播完）
        if sprite.has_action:
            return

        self._idle_timer += dt
        if self._idle_timer >= self._next_action_at:
            self._idle_timer = 0.0
            self._next_action_at = self._next_interval(sprite)
            if mouse_far:
                self._start_autonomous_activity(sprite)
            # 鼠标较近但无需捕猎时，动作收敛一些。
            elif random.random() < 0.5:
                self._start_wander(sprite, config.IDLE_WANDER_RADIUS_PX)
            else:
                self._start_idle_action(sprite)
            return

        # 没有动作且计时未到：偶尔看看四周（轻微头转）
        if not sprite.has_action:
            sprite.pose.head_turn = 0.3 * (
                1 if int(sprite.x * 0.1) % 2 == 0 else -1
            )
            sprite.pose.tail_wag_phase += dt * 1.5

    def _next_interval(self, sprite) -> float:
        """活泼的猫更频繁地产生自己的活动。"""
        base = random.uniform(*config.IDLE_ACTION_INTERVAL_S)
        return base * (1.2 - 0.45 * sprite.personality.liveliness)

    def _start_autonomous_activity(self, sprite) -> None:
        roll = random.random()
        poop_p = config.AUTONOMOUS_POOP_PROB
        zoomies_p = config.AUTONOMOUS_ZOOMIES_PROB * (0.5 + sprite.personality.liveliness)
        play_p = config.AUTONOMOUS_PLAY_PROB * (0.5 + sprite.personality.playfulness)
        if roll < poop_p:
            sprite.play(make_action("poop", sprite=sprite))
        elif roll < poop_p + zoomies_p:
            self._zoomies_remaining = random.randint(2, 4)
            self._continue_zoomies(sprite)
        elif roll < poop_p + zoomies_p + play_p:
            # 没有猎物也会扑影子、拍空气、翻滚，自娱自乐。
            target = self._random_target(sprite, 80)
            sprite.play(make_action("play", sprite=sprite, target=target))
        elif roll < 0.85:
            self._start_wander(sprite, config.AUTONOMOUS_ROAM_RADIUS_PX)
        else:
            self._start_idle_action(sprite)

    def _continue_zoomies(self, sprite) -> None:
        if self._zoomies_remaining <= 0 or sprite.fsm.current_name != "idle":
            return
        self._zoomies_remaining -= 1
        target = self._random_target(sprite, config.AUTONOMOUS_ROAM_RADIUS_PX)
        sprite.play(
            make_action("walk", sprite=sprite, target=target,
                        speed_px_s=config.AUTONOMOUS_RUN_SPEED_PX_S),
            on_done=lambda: self._continue_zoomies(sprite),
        )

    def _random_target(self, sprite, radius: float):
        angle = random.uniform(0, math.tau)
        r = random.uniform(radius * 0.35, radius)
        tx = sprite.x + math.cos(angle) * r
        ty = sprite.y + math.sin(angle) * r
        left, top, right, bottom = sprite.world_bounds
        margin = sprite.size_px * 0.55
        return (
            clamp(tx, left + margin, right - margin),
            clamp(ty, top + margin, bottom - margin),
        )

    def _start_wander(self, sprite, radius: float) -> None:
        """在"家"点附近随机选一个目标走过去。"""
        target = self._random_target(sprite, radius)
        sprite.play(make_action("walk", sprite=sprite, target=target))

    def _start_idle_action(self, sprite) -> None:
        """按权重选一个空闲小动作播放。groom 走独立状态。"""
        choice = weighted_choice(IDLE_ACTIONS, sprite.personality)
        family = choice["family"]
        if family == "groom":
            # groom 是独立状态（被打断逻辑不同）
            sprite.fsm.transition_to("grooming")
            return
        sprite.play(make_action(family, choice["variant"], sprite=sprite))
