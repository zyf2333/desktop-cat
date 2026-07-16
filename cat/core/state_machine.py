"""轻量有限状态机（FSM）。

设计目标：零依赖、完全可控、模型无关。一个 FSM 持有若干 State，
任一时刻处于一个"当前状态"，每帧由 update 驱动当前状态；
状态可通过 transition_to 切换。

状态用名字（str）登记，便于跨模型/跨文件引用与测试。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from .pet_sprite import PetSprite


class State:
    """状态基类。子类按需重写钩子，无需全部重写。"""

    name: str = "base"

    def on_enter(self, sprite: "PetSprite") -> None:
        """进入此状态时调用一次。"""

    def on_exit(self, sprite: "PetSprite") -> None:
        """离开此状态时调用一次。"""

    def update(self, sprite: "PetSprite", dt: float, mouse_state) -> None:
        """每帧调用。可在内部通过 sprite.fsm.transition_to(...) 切换状态。

        Args:
            sprite: 宠物实体
            dt: 距离上一帧的秒数
            mouse_state: 鼠标状态快照（位置、速度等），由 MouseTracker 提供
        """


class StateMachine:
    """通用有限状态机。"""

    def __init__(self, sprite: "PetSprite") -> None:
        self.sprite = sprite
        self._states: Dict[str, State] = {}
        self._current: Optional[State] = None

    # ---- 注册 ----
    def add(self, state: State) -> None:
        """登记一个状态实例。"""
        if state.name in self._states:
            raise ValueError(f"状态 '{state.name}' 已存在，不能重复注册")
        self._states[state.name] = state

    def start(self, initial_name: str) -> None:
        """启动状态机，进入初始状态。"""
        if initial_name not in self._states:
            raise KeyError(f"初始状态 '{initial_name}' 未注册")
        self._current = self._states[initial_name]
        self._current.on_enter(self.sprite)

    # ---- 查询 ----
    @property
    def current_name(self) -> Optional[str]:
        return self._current.name if self._current else None

    @property
    def current(self) -> Optional[State]:
        return self._current

    def get(self, name: str) -> State:
        return self._states[name]

    # ---- 驱动 ----
    def update(self, dt: float, mouse_state) -> None:
        """每帧驱动当前状态。"""
        if self._current is None:
            return
        self._current.update(self.sprite, dt, mouse_state)

    # ---- 切换 ----
    def transition_to(self, name: str) -> bool:
        """切换到目标状态。目标不存在返回 False，否则返回 True。

        切换到当前同名状态视为无操作（返回 True），避免 on_exit/on_enter 抖动。
        """
        target = self._states.get(name)
        if target is None:
            return False
        if self._current is target:
            return True
        if self._current is not None:
            self._current.on_exit(self.sprite)
        self._current = target
        self._current.on_enter(self.sprite)
        return True
