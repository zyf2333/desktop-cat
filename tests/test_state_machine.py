"""状态机单元测试。

用纯 Python 的假 sprite（任何对象都行，FSM 不关心其类型）验证：
- 状态注册、启动、切换
- on_enter/on_exit 钩子顺序
- 切换到当前状态不抖动
- 切换到未注册状态返回 False
"""
from __future__ import annotations

from cat.core.state_machine import State, StateMachine


class FakeSprite:
    """FSM 只把它透传给 State，不需要任何真实字段。"""


class CountingState(State):
    """记录 enter/exit/update 调用次数，用于断言。"""

    def __init__(self, name):
        self.name = name
        self.enters = 0
        self.exits = 0
        self.updates = 0

    def on_enter(self, sprite):
        self.enters += 1

    def on_exit(self, sprite):
        self.exits += 1

    def update(self, sprite, dt, mouse_state):
        self.updates += 1


def test_register_and_start():
    fsm = StateMachine(FakeSprite())
    a = CountingState("a")
    fsm.add(a)
    fsm.start("a")
    assert fsm.current_name == "a"
    assert a.enters == 1  # start 触发 on_enter


def test_duplicate_register_raises():
    fsm = StateMachine(FakeSprite())
    fsm.add(CountingState("a"))
    try:
        fsm.add(CountingState("a"))
        assert False, "应抛 ValueError"
    except ValueError:
        pass


def test_start_unknown_state_raises():
    fsm = StateMachine(FakeSprite())
    try:
        fsm.start("nope")
        assert False, "应抛 KeyError"
    except KeyError:
        pass


def test_transition_calls_hooks_in_order():
    fsm = StateMachine(FakeSprite())
    a = CountingState("a")
    b = CountingState("b")
    fsm.add(a)
    fsm.add(b)
    fsm.start("a")
    assert a.enters == 1 and a.exits == 0
    ok = fsm.transition_to("b")
    assert ok is True
    assert a.exits == 1      # 离开 a
    assert b.enters == 1     # 进入 b
    assert fsm.current_name == "b"


def test_transition_to_same_state_noop():
    fsm = StateMachine(FakeSprite())
    a = CountingState("a")
    fsm.add(a)
    fsm.start("a")
    ok = fsm.transition_to("a")
    assert ok is True
    assert a.enters == 1  # 没有再次 enter
    assert a.exits == 0


def test_transition_to_unknown_returns_false():
    fsm = StateMachine(FakeSprite())
    a = CountingState("a")
    fsm.add(a)
    fsm.start("a")
    ok = fsm.transition_to("ghost")
    assert ok is False
    assert fsm.current_name == "a"  # 状态未变


def test_update_drives_current_state():
    fsm = StateMachine(FakeSprite())
    a = CountingState("a")
    fsm.add(a)
    fsm.start("a")
    fsm.update(0.016, None)
    fsm.update(0.016, None)
    assert a.updates == 2


def test_update_before_start_does_nothing():
    fsm = StateMachine(FakeSprite())
    a = CountingState("a")
    fsm.add(a)
    # 未 start 就 update，不应崩溃，也不应驱动任何状态
    fsm.update(0.016, None)
    assert a.updates == 0


def test_state_self_transition_via_update():
    """状态在 update 内主动触发切换。"""
    sprite = FakeSprite()
    fsm = StateMachine(sprite)
    sprite.fsm = fsm  # 让状态能通过 sprite.fsm 访问

    class GotoB(State):
        name = "goto_b"

        def update(self, sprite, dt, mouse_state):
            sprite.fsm.transition_to("b")

    b = CountingState("b")
    fsm.add(GotoB())
    fsm.add(b)
    fsm.start("goto_b")
    fsm.update(0.016, None)
    assert fsm.current_name == "b"
    assert b.enters == 1
