"""状态判定条件 _conditions 的单元测试（纯函数）。"""
from __future__ import annotations

from cat import config
from cat.core.model import get_model
from cat.core.pet_sprite import PetSprite
from cat.models.cat.states._conditions import (
    dist_to_mouse,
    in_alert_range,
    lost_mouse,
    mouse_pos,
)
from cat.mouse_tracker import MouseState


def make_sprite(x=500.0, y=500.0):
    model = get_model("cat")
    return PetSprite(model, x=x, y=y, size_px=config.PET_SIZE_PX)


def ms_at(pos, **kw):
    defaults = dict(speed_smooth=400.0, is_escaping=False, still_seconds=0.0, moving=True)
    defaults.update(kw)
    return MouseState(pos=pos, **defaults)


class TestDistToMouse:
    def test_basic(self):
        s = make_sprite(0, 0)
        assert dist_to_mouse(s, ms_at((3, 4))) == 5.0

    def test_none_mouse_returns_inf(self):
        s = make_sprite()
        assert dist_to_mouse(s, None) == float("inf")


class TestAlertRange:
    def test_inside_and_moving(self):
        s = make_sprite(0, 0)
        assert in_alert_range(s, ms_at((100, 0))) is True

    def test_inside_but_still(self):
        s = make_sprite(0, 0)
        assert in_alert_range(s, ms_at((100, 0), moving=False)) is False

    def test_outside(self):
        s = make_sprite(0, 0)
        assert in_alert_range(s, ms_at((500, 0))) is False  # > 220

    def test_none_mouse(self):
        s = make_sprite()
        assert in_alert_range(s, None) is False


class TestLostMouse:
    def test_within_range_not_lost(self):
        s = make_sprite(0, 0)
        assert lost_mouse(s, ms_at((200, 0))) is False

    def test_beyond_lose_range_lost(self):
        s = make_sprite(0, 0)
        assert lost_mouse(s, ms_at((500, 0))) is True  # > 420

    def test_escaping_is_lost(self):
        s = make_sprite(0, 0)
        assert lost_mouse(s, ms_at((100, 0), is_escaping=True)) is True

    def test_none_mouse_lost(self):
        s = make_sprite()
        assert lost_mouse(s, None) is True


class TestMousePos:
    def test_returns_mouse_state_pos(self):
        s = make_sprite(0, 0)
        s.mouse_state = ms_at((123, 456))
        assert mouse_pos(s) == (123, 456)

    def test_fallback_to_sprite_pos(self):
        s = make_sprite(789, 0)
        s.mouse_state = None
        assert mouse_pos(s) == (789, 0)
