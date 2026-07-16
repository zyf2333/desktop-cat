"""几何与缓动工具（纯函数）。

所有函数不依赖任何 UI/Qt 对象，便于单元测试。
坐标采用屏幕像素，y 轴向下（与 Qt 一致）。
"""
from __future__ import annotations

import math
from collections import deque
from typing import Deque, Tuple

Point = Tuple[float, float]


def distance(a: Point, b: Point) -> float:
    """两点欧氏距离。"""
    return math.hypot(b[0] - a[0], b[1] - a[1])


def direction(from_: Point, to: Point) -> Point:
    """返回 from->to 的单位向量；若两点重合返回 (0, 0)。"""
    dx, dy = to[0] - from_[0], to[1] - from_[1]
    d = math.hypot(dx, dy)
    if d == 0:
        return (0.0, 0.0)
    return (dx / d, dy / d)


def move_towards(pos: Point, target: Point, max_step: float) -> Point:
    """把 pos 朝 target 移动最多 max_step 像素，返回新位置。

    不会越过 target；若已到达（距离<=max_step）则返回 target 本身。
    """
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    d = math.hypot(dx, dy)
    if d <= max_step or d == 0:
        return (target[0], target[1])
    return (pos[0] + dx / d * max_step, pos[1] + dy / d * max_step)


def clamp(value: float, low: float, high: float) -> float:
    """将 value 限制在 [low, high]。"""
    return max(low, min(high, value))


# ---- 缓动函数 ----
def ease_in_out_cubic(t: float) -> float:
    """先加速后减速的三次缓动。t∈[0,1]。"""
    t = clamp(t, 0.0, 1.0)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_cubic(t: float) -> float:
    """快速起步、缓慢结束。t∈[0,1]。"""
    t = clamp(t, 0.0, 1.0)
    return 1 - (1 - t) ** 3


def ease_out_back(t: float, s: float = 1.7) -> float:
    """略微过冲再回弹，适合"扑"的收尾。t∈[0,1]。"""
    t = clamp(t, 0.0, 1.0)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


# ---- 滑动平均速度 ----
class SpeedSmoother:
    """用滑动窗口计算鼠标平均速度（px/s），抑制瞬时抖动。

    存储最近 window_seconds 秒内的位移样本，按总位移/总时间得出平均速度。
    """

    def __init__(self, window_seconds: float = 0.3) -> None:
        self.window = window_seconds
        # 每个元素：(时间戳秒, (x, y))
        self._samples: Deque[Tuple[float, Point]] = deque()

    def reset(self) -> None:
        self._samples.clear()

    def push(self, t: float, pos: Point) -> None:
        """记录一个采样点。同时丢弃窗口外的旧样本。"""
        self._samples.append((t, pos))
        cutoff = t - self.window
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def speed(self) -> float:
        """返回窗口内的平均速度（px/s）。样本不足时返回 0。"""
        if len(self._samples) < 2:
            return 0.0
        t0, p0 = self._samples[0]
        t1, p1 = self._samples[-1]
        dt = t1 - t0
        if dt <= 0:
            return 0.0
        return distance(p0, p1) / dt
