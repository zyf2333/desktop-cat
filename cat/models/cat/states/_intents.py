"""二维决策：把（距离 × 速度 × 个性）映射到"意图"。

集中所有"猫现在该做什么"的判定，替代散落在各 State 里的距离/速度阈值比较。
所有状态共享一致的决策，调手感只改 config + decide_intent。

意图与状态映射（状态机里 transition_to 时用）：
    IGNORE  → 留在 idle
    ALERT   → alert
    STALK   → stalking
    CHASE   → chasing
    POUNCE  → pouncing
    PLAY    → playing
    LOST    → confused
"""
from __future__ import annotations

import math
from enum import Enum

from cat import config


class Intent(Enum):
    IGNORE = "ignore"
    ALERT = "alert"
    STALK = "stalk"
    CHASE = "chase"
    POUNCE = "pounce"
    PLAY = "play"
    LOST = "lost"


def decide_intent(sprite, mouse_state) -> Intent:
    """根据 (距离, 速度, 个性) 决定当前意图。

    mouse_state 为 None 或鼠标静止时返回 IGNORE（除非完全无鼠标→LOST 不在这里处理）。
    所有距离/速度阈值受个性调节。
    """
    if mouse_state is None:
        return Intent.IGNORE

    p = sprite.personality
    d = math.hypot(mouse_state.pos[0] - sprite.x, mouse_state.pos[1] - sprite.y)
    speed = mouse_state.speed_smooth

    # 个性化阈值
    # 警觉度高的猫 ALERT 范围更大（0.7x ~ 1.3x）
    alert_r = config.ALERT_RADIUS_PX * (0.7 + 0.6 * p.alertness)
    # 关注范围同样受警觉度影响
    lose_r = config.LOSE_RADIUS_PX * (0.8 + 0.4 * p.alertness)
    # 速度判定也微调
    stalk_speed = config.STALK_MOUSE_SPEED_PX_S * (0.8 + 0.4 * p.patience)  # 有耐心的猫更愿意潜行慢目标
    pounce_speed = config.POUNCE_MOUSE_SPEED_PX_S

    # ---- 1. 丢失：超出关注范围 或 高速甩脱 ----
    if mouse_state.is_escaping or d > lose_r:
        return Intent.LOST

    # ---- 2. 太远且鼠标不动 → 无视 ----
    if not mouse_state.moving and d > alert_r:
        return Intent.IGNORE

    # ---- 3. 在关注范围内 ----
    # 近距离优先判定（PLAY > POUNCE）
    if d <= config.PLAY_DIST_PX:
        return Intent.PLAY
    if d <= config.POUNCE_DIST_PX and speed > pounce_speed:
        # 近 + 快 → 果断扑
        return Intent.POUNCE
    if d > alert_r:
        # 在关注范围外缘但还在 lose_r 内：只对移动有反应
        if mouse_state.moving:
            return Intent.ALERT
        return Intent.IGNORE
    # 在警觉范围内：根据鼠标速度选 STALK/CHASE
    if speed < stalk_speed:
        return Intent.STALK
    return Intent.CHASE
