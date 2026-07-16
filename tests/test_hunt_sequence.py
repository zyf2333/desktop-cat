"""捕猎行为序列与困惑判定的单元测试。

用一个 FakeSprite + 真实状态机驱动，模拟鼠标状态变化，验证：
- 完整捕猎序列 idle → alert → noticed → stalking → pouncing → ...
- 困惑触发（距离超出 或 甩脱）
- 警觉范围触发
"""
from __future__ import annotations

from cat import config
from cat.core.model import get_model
from cat.core.pet_sprite import PetSprite
from cat.models.cat.poses import CatPose
from cat.mouse_tracker import MouseState


def make_sprite(x=500.0, y=500.0):
    """用真实猫模型创建 sprite（含真实状态机）。"""
    model = get_model("cat")
    return PetSprite(model, x=x, y=y, size_px=config.PET_SIZE_PX)


def mouse_at(pos, **kw):
    """构造一个 MouseState。"""
    defaults = dict(speed_smooth=400.0, is_escaping=False, still_seconds=0.0, moving=True)
    defaults.update(kw)
    return MouseState(pos=pos, **defaults)


def drive(sprite, mouse_state, frames=60, dt=1/60):
    """驱动若干帧。"""
    for _ in range(frames):
        sprite.update(dt, mouse_state)


class TestAlertRange:
    def test_mouse_outside_alert_range_stays_idle(self):
        sprite = make_sprite()
        # 鼠标在远处移动（超出警觉半径 220）
        ms = mouse_at((sprite.x + 500, sprite.y))
        drive(sprite, ms, frames=30)
        assert sprite.fsm.current_name == "idle"

    def test_mouse_inside_alert_range_triggers_alert(self):
        sprite = make_sprite()
        # 鼠标在警觉半径内且移动
        ms = mouse_at((sprite.x + 100, sprite.y))
        drive(sprite, ms, frames=5)
        assert sprite.fsm.current_name == "alert"


class TestHuntSequence:
    def test_full_sequence_idle_to_chasing(self):
        """鼠标先靠近触发警觉，进入捕猎链；之后保持中等距离持续移动，
        最终应进入追逐/扑击（不应卡在 idle 或早期状态）。"""
        sprite = make_sprite()
        # 第一步：鼠标进入警觉范围（150px），触发 alert
        ms_close = mouse_at((sprite.x + 150, sprite.y))
        drive(sprite, ms_close, frames=80)  # 走过 alert→noticed→stalking
        # 此时应在 stalking 或已转 chasing/pouncing
        assert sprite.fsm.current_name in ("stalking", "chasing", "pouncing")

        # 第二步：鼠标保持中等距离持续移动，验证能持续在追逐链中
        # 用一个会"逃跑"的鼠标：始终在猫前方 150px
        for _ in range(200):
            run_ms = mouse_at((sprite.x + 150, sprite.y))
            sprite.update(1/60, run_ms)
        assert sprite.fsm.current_name in ("chasing", "pouncing", "stalking")

    def test_alert_progresses_to_noticed(self):
        sprite = make_sprite()
        ms = mouse_at((sprite.x + 100, sprite.y))
        drive(sprite, ms, frames=5)
        assert sprite.fsm.current_name == "alert"
        # 警觉持续 0.4-0.8s，约 30-50 帧后转 noticed
        drive(sprite, ms, frames=60)
        assert sprite.fsm.current_name in ("noticed", "stalking", "chasing", "pouncing")


class TestConfusion:
    def test_mouse_far_away_during_hunt_triggers_confused(self):
        """捕猎中鼠标突然跑出关注范围 → 困惑。"""
        sprite = make_sprite()
        # 先触发警觉
        ms = mouse_at((sprite.x + 100, sprite.y))
        drive(sprite, ms, frames=5)
        assert sprite.fsm.current_name == "alert"
        # 鼠标突然跑到很远（超出 LOSE_RADIUS 420）
        ms_far = mouse_at((sprite.x + 1000, sprite.y))
        drive(sprite, ms_far, frames=3)
        assert sprite.fsm.current_name == "confused"

    def test_escape_speed_triggers_confused(self):
        """捕猎中鼠标高速甩脱 → 困惑。"""
        sprite = make_sprite()
        ms = mouse_at((sprite.x + 100, sprite.y))
        drive(sprite, ms, frames=5)
        assert sprite.fsm.current_name == "alert"
        # 鼠标高速甩脱（在范围内但 is_escaping）
        ms_fast = mouse_at((sprite.x + 100, sprite.y), is_escaping=True)
        drive(sprite, ms_fast, frames=3)
        assert sprite.fsm.current_name == "confused"

    def test_confused_returns_to_idle_after_duration(self):
        """困惑持续一段后回 idle。"""
        sprite = make_sprite()
        ms = mouse_at((sprite.x + 100, sprite.y))
        drive(sprite, ms, frames=5)
        ms_far = mouse_at((sprite.x + 1000, sprite.y))
        drive(sprite, ms_far, frames=3)
        assert sprite.fsm.current_name == "confused"
        # 困惑持续 1.2-2.2s，驱动足够久（鼠标保持远处不动）
        ms_gone = mouse_at((sprite.x + 1000, sprite.y), moving=False, speed_smooth=0)
        drive(sprite, ms_gone, frames=200)  # ~3.3s
        assert sprite.fsm.current_name == "idle"


class TestPoseFlags:
    def test_alert_sets_alerted_flag(self):
        sprite = make_sprite()
        ms = mouse_at((sprite.x + 100, sprite.y))
        drive(sprite, ms, frames=5)
        assert sprite.fsm.current_name == "alert"
        assert sprite.pose.alerted is True
        assert sprite.pose.ear_alert > 0.5

    def test_confused_sets_confused_flag(self):
        sprite = make_sprite()
        ms = mouse_at((sprite.x + 100, sprite.y))
        drive(sprite, ms, frames=5)
        ms_far = mouse_at((sprite.x + 1000, sprite.y))
        drive(sprite, ms_far, frames=3)
        assert sprite.fsm.current_name == "confused"
        assert sprite.pose.confused is True
