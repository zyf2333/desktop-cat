"""鼠标状态追踪。

以固定频率轮询全局鼠标位置，计算瞬时速度与滑动平均速度，
并维护"连续高速时长"用于甩脱判定。

输出一个不可变的 MouseState 快照，供 FSM 每帧消费。

不使用全局钩子（pynput 等），避免权限问题与跨平台差异。
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Tuple

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QCursor

from cat import config
from cat.utils.geometry import SpeedSmoother

Point = Tuple[float, float]


@dataclass(frozen=True)
class MouseState:
    """某一时刻的鼠标状态快照。"""

    pos: Point                  # 全局鼠标坐标
    speed_smooth: float         # 滑动平均速度（px/s），用于甩脱判定
    is_escaping: bool           # 是否处于"甩脱"状态（高速持续超阈值）
    still_seconds: float        # 鼠标已连续静止（速度<阈值）的秒数
    moving: bool                # 当前是否在移动（速度>静止阈值）


class MouseTracker(QObject):
    """轮询全局鼠标，对外发射 MouseState。"""

    #: 每次采样后发射最新状态。
    state_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._tick)

        self._smoother = SpeedSmoother(config.MOUSE_SMOOTH_WINDOW_S)
        self._last_pos: Point = self._current_cursor()
        self._last_t: float = time.monotonic()

        self._escape_accum = 0.0     # 连续高速累积秒数
        self._still_accum = 0.0      # 连续静止累积秒数

    # ---- 生命周期 ----
    def start(self) -> None:
        interval_ms = int(1000 / config.MOUSE_POLL_HZ)
        # 重置基线，避免启动瞬间算出巨大速度
        self._last_pos = self._current_cursor()
        self._last_t = time.monotonic()
        self._smoother.reset()
        self._escape_accum = 0.0
        self._still_accum = 0.0
        self._timer.start(interval_ms)

    def stop(self) -> None:
        self._timer.stop()

    # ---- 采样 ----
    def _current_cursor(self) -> Point:
        p = QCursor.pos()
        return (p.x(), p.y())

    def _tick(self) -> None:
        now = time.monotonic()
        dt = now - self._last_t
        pos = self._current_cursor()

        self._smoother.push(now, pos)
        speed = self._smoother.speed()

        # 甩脱累积：滑动平均速度超过阈值则累加，否则清零
        if speed >= config.ESCAPE_SPEED_PX_S:
            self._escape_accum += dt
        else:
            self._escape_accum = 0.0
        is_escaping = self._escape_accum >= config.ESCAPE_DURATION_S
        if is_escaping:
            # 一旦判定甩脱，持续保持直到速度降下来（见 else 分支会清零累积）
            pass

        # 静止累积
        if speed < config.MOUSE_STILL_THRESHOLD_PX_S:
            self._still_accum += dt
        else:
            self._still_accum = 0.0

        state = MouseState(
            pos=pos,
            speed_smooth=speed,
            is_escaping=is_escaping,
            still_seconds=self._still_accum,
            moving=speed >= config.MOUSE_STILL_THRESHOLD_PX_S,
        )
        self._last_pos = pos
        self._last_t = now
        self.state_changed.emit(state)
