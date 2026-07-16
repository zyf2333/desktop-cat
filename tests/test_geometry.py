"""几何/缓动工具的单元测试（纯函数，无 Qt）。"""
from __future__ import annotations

import math

from cat.utils.geometry import (
    SpeedSmoother,
    clamp,
    direction,
    distance,
    ease_in_out_cubic,
    ease_out_back,
    ease_out_cubic,
    move_towards,
)


def test_distance_basic():
    assert distance((0, 0), (3, 4)) == 5.0
    assert distance((1, 1), (1, 1)) == 0.0


def test_direction_unit_vector():
    dx, dy = direction((0, 0), (10, 0))
    assert math.isclose(dx, 1.0) and math.isclose(dy, 0.0)
    dx, dy = direction((0, 0), (0, -5))
    assert math.isclose(dx, 0.0) and math.isclose(dy, -1.0)


def test_direction_coincident_returns_zero():
    assert direction((2, 2), (2, 2)) == (0.0, 0.0)


def test_move_towards_partial():
    # 距离 10，移动 3 → 应朝目标走 3
    nx, ny = move_towards((0, 0), (10, 0), 3)
    assert math.isclose(nx, 3.0) and math.isclose(ny, 0.0)


def test_move_towards_overshoot_clamps_to_target():
    # 步长大于距离，应直接到目标，不越过
    nx, ny = move_towards((0, 0), (2, 0), 100)
    assert (nx, ny) == (2.0, 0.0)


def test_move_towards_at_target():
    nx, ny = move_towards((5, 5), (5, 5), 10)
    assert (nx, ny) == (5.0, 5.0)


def test_clamp():
    assert clamp(5, 0, 10) == 5
    assert clamp(-3, 0, 10) == 0
    assert clamp(15, 0, 10) == 10
    assert clamp(0, 0, 10) == 0


def test_easing_endpoints():
    # 所有缓动函数在端点应返回 0 和 1（允许浮点误差）
    assert math.isclose(ease_in_out_cubic(0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(ease_in_out_cubic(1.0), 1.0, abs_tol=1e-9)
    assert math.isclose(ease_out_cubic(0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(ease_out_cubic(1.0), 1.0, abs_tol=1e-9)
    assert math.isclose(ease_out_back(0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(ease_out_back(1.0), 1.0, abs_tol=1e-9)


def test_easing_monotonic():
    # ease_out_cubic 应单调递增
    prev = -1.0
    for i in range(11):
        v = ease_out_cubic(i / 10.0)
        assert v >= prev
        prev = v


def test_ease_out_back_overshoots():
    # ease_out_back 中段应超过 1（回弹特性）
    assert ease_out_back(0.85) > 1.0


def test_speed_smoother_low_speed_for_slow_movement():
    s = SpeedSmoother(window_seconds=0.3)
    # 慢速移动：每 0.1s 移动 1px = 10px/s
    s.push(0.0, (0, 0))
    s.push(0.1, (1, 0))
    s.push(0.2, (2, 0))
    s.push(0.3, (3, 0))
    assert s.speed() < 30.0  # 远低于甩脱阈值


def test_speed_smoother_high_speed_for_fast_movement():
    s = SpeedSmoother(window_seconds=0.3)
    # 快速移动：每 0.01s 移动 50px
    for i in range(31):
        s.push(i * 0.01, (i * 50, 0))
    assert s.speed() > 2500.0  # 触发甩脱阈值


def test_speed_smoother_empty_returns_zero():
    s = SpeedSmoother()
    assert s.speed() == 0.0
    s.push(0.0, (0, 0))
    assert s.speed() == 0.0  # 只有一个点


def test_speed_smoother_drops_old_samples():
    s = SpeedSmoother(window_seconds=0.3)
    # 先快速移动，然后停下来
    for i in range(5):
        s.push(i * 0.05, (i * 100, 0))  # 0~0.2s
    # 旧样本应被保留（在窗口内）
    assert s.speed() > 0
    # 推进到很久之后，旧样本被丢弃
    s.push(10.0, (1000, 0))
    # 只剩最后一个点（10.0 时刻），速度应为 0
    assert s.speed() == 0.0
