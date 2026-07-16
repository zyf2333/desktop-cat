"""猫的动作库。

每个动作一个文件，实现 cat.core.action.Action。
新增动作：新建一个文件 + 在 ACTIONS 注册一行。

约定：动作只修改 pose 的字段 + sprite 的位置/朝向，不自行决定状态切换。
完成时调用 self.finish() 触发 on_done 回调（由 State 设置）。
"""
from __future__ import annotations

from cat.models.cat.actions._helpers import reset_to_stand
from cat.models.cat.actions.groom import GroomAction
from cat.models.cat.actions.pounce import PounceAction
from cat.models.cat.actions.run import RunAction
from cat.models.cat.actions.sit import SitAction
from cat.models.cat.actions.sleep import SleepAction
from cat.models.cat.actions.stretch import StretchAction
from cat.models.cat.actions.walk import WalkAction

# 动作名 → Action 类。State 用这些名字创建实例。
ACTIONS = {
    "walk": WalkAction,
    "run": RunAction,
    "pounce": PounceAction,
    "sit": SitAction,
    "sleep": SleepAction,
    "groom": GroomAction,
    "stretch": StretchAction,
}

# IDLE 状态可随机挑选的"小动作"（不含 walk/run/pounce 这些位移类）
IDLE_IDLE_ACTIONS = ["sit", "groom", "stretch"]


__all__ = [
    "ACTIONS",
    "IDLE_IDLE_ACTIONS",
    "reset_to_stand",
    "WalkAction",
    "RunAction",
    "PounceAction",
    "SitAction",
    "SleepAction",
    "GroomAction",
    "StretchAction",
]
