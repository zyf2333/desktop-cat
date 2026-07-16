"""状态机共享的判定工具（纯函数）。

集中所有"猫与鼠标关系"的判定，避免在多个 State 里重复，
也便于单元测试。
"""
from __future__ import annotations

import math

from cat import config


def dist_to_mouse(sprite, mouse_state) -> float:
    """猫中心到鼠标的欧氏距离。mouse_state 为 None 时返回无穷大。"""
    if mouse_state is None:
        return float("inf")
    return math.hypot(mouse_state.pos[0] - sprite.x, mouse_state.pos[1] - sprite.y)


def in_alert_range(sprite, mouse_state) -> bool:
    """鼠标是否进入猫的警觉范围（且在移动）。"""
    if mouse_state is None or not mouse_state.moving:
        return False
    return dist_to_mouse(sprite, mouse_state) <= config.ALERT_RADIUS_PX


def lost_mouse(sprite, mouse_state) -> bool:
    """猫是否"丢失"鼠标：超出关注范围，或鼠标高速甩脱。

    用于追逐/警觉中判定是否进入困惑。
    """
    if mouse_state is None:
        return True
    if mouse_state.is_escaping:
        return True
    return dist_to_mouse(sprite, mouse_state) > config.LOSE_RADIUS_PX


def mouse_pos(sprite):
    """获取当前鼠标位置，mouse_state 缺失时返回猫当前位置。"""
    if sprite.mouse_state is not None:
        return sprite.mouse_state.pos
    return (sprite.x, sprite.y)
