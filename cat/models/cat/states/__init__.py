"""猫的状态机装配。

build_cat_state_machine 把五个状态注册进 StateMachine 并指定初始状态 idle。
状态间的转换由各 State 自己在 update 中根据 mouse_state 决定。

新增状态：新建一个 State 子类 + 在这里 add + 在相关 State 里加 transition_to。
"""
from __future__ import annotations

from cat.core.state_machine import StateMachine
from cat.models.cat.states.chasing_state import ChasingState
from cat.models.cat.states.grooming_state import GroomingState
from cat.models.cat.states.idle_state import IdleState
from cat.models.cat.states.pouncing_state import PouncingState
from cat.models.cat.states.sleeping_state import SleepingState


def build_cat_state_machine(sprite) -> StateMachine:
    fsm = StateMachine(sprite)
    fsm.add(IdleState())
    fsm.add(ChasingState())
    fsm.add(PouncingState())
    fsm.add(SleepingState())
    fsm.add(GroomingState())
    # 初始状态
    fsm.start("idle")
    return fsm


__all__ = [
    "build_cat_state_machine",
    "IdleState",
    "ChasingState",
    "PouncingState",
    "SleepingState",
    "GroomingState",
]
