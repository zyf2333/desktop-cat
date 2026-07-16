"""猫的状态机装配。

完整捕猎序列（8 状态）：
  idle → alert → noticed → stalking → pouncing → chasing → ... → confused → idle
                                                              ↘ sleeping

各状态的转换由 State 自己在 update 中根据 mouse_state 决定。
新增状态：新建一个 State 子类 + 在这里 add + 在相关 State 里加 transition_to。
"""
from __future__ import annotations

from cat.core.state_machine import StateMachine
from cat.models.cat.states.alert_state import AlertState
from cat.models.cat.states.chasing_state import ChasingState
from cat.models.cat.states.confused_state import ConfusedState
from cat.models.cat.states.grooming_state import GroomingState
from cat.models.cat.states.idle_state import IdleState
from cat.models.cat.states.notice_state import NoticeState
from cat.models.cat.states.playing_state import PlayingState
from cat.models.cat.states.pouncing_state import PouncingState
from cat.models.cat.states.sleeping_state import SleepingState
from cat.models.cat.states.stalking_state import StalkingState


def build_cat_state_machine(sprite) -> StateMachine:
    fsm = StateMachine(sprite)
    # 空闲
    fsm.add(IdleState())
    # 捕猎链
    fsm.add(AlertState())
    fsm.add(NoticeState())
    fsm.add(StalkingState())
    fsm.add(PouncingState())
    fsm.add(ChasingState())
    # 玩弄（逗猫棒玩法）
    fsm.add(PlayingState())
    # 困惑
    fsm.add(ConfusedState())
    # 生理
    fsm.add(SleepingState())
    fsm.add(GroomingState())
    # 初始状态
    fsm.start("idle")
    return fsm


__all__ = [
    "build_cat_state_machine",
    "IdleState",
    "AlertState",
    "NoticeState",
    "StalkingState",
    "PouncingState",
    "ChasingState",
    "PlayingState",
    "ConfusedState",
    "SleepingState",
    "GroomingState",
]
