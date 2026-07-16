"""Action（动作）抽象。

一个 Action 是一个有限时长的原子行为（走、跑、扑、坐、睡、舔毛……）。
State 通过 action 控制宠物的位置/朝向/姿态；Action 完成后通过回调通知 State。

设计要点：
- Action 只关心"这段时间内怎么变化"，不关心为何进入（决策由 State 负责）。
- pose 是模型自定义的不透明对象，Action 直接读写它的字段，框架不解析。
- 一个 Action 实例一次只服务一次执行；如需重复，每次 start 重新生成。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from .pet_sprite import PetSprite


class Action:
    """动作基类。"""

    name: str = "base"

    def __init__(self) -> None:
        # 完成回调。State 在 start 时设置，动作结束时触发。
        self.on_done: Optional[Callable[[], None]] = None
        self._done = False

    def start(self, sprite: "PetSprite") -> None:
        """动作开始。重写时务必调用 super().start() 以重置完成标记。"""
        self._done = False

    def update(self, sprite: "PetSprite", dt: float) -> None:
        """每帧推进动作。"""

    def is_done(self) -> bool:
        """动作是否已结束。"""
        return self._done

    # ---- 完成通知 ----
    def finish(self) -> None:
        """子类在动作自然结束时调用，触发 on_done 回调。"""
        if self._done:
            return
        self._done = True
        if self.on_done is not None:
            self.on_done()
