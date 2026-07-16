"""玩腻走开行为的单元测试。

验证：PLAYING 中鼠标静止超过阈值 → 猫回 idle（走开），且冷却期内不立即回去。
"""
from __future__ import annotations

import time

from cat import config
from cat.core.model import get_model
from cat.core.pet_sprite import PetSprite
from cat.mouse_tracker import MouseState


def make_sprite(x=500.0, y=500.0):
    return PetSprite(get_model("cat"), x=x, y=y, size_px=config.PET_SIZE_PX)


def ms_at(pos, **kw):
    d = dict(speed_smooth=400.0, is_escaping=False, still_seconds=0.0, moving=True)
    d.update(kw)
    return MouseState(pos=pos, **d)


def drive(sprite, mouse_state, frames, dt=1/60):
    for _ in range(frames):
        sprite.update(dt, mouse_state)


class TestBoredLeave:
    def test_playing_leaves_when_mouse_still(self):
        """PLAYING 中鼠标静止超过阈值 → 回 idle。"""
        sprite = make_sprite()
        sprite.fsm.transition_to("playing")
        assert sprite.fsm.current_name == "playing"
        # 鼠标贴近但静止，驱动超过 bored_after（默认 2.5s * 个性系数）
        still_ms = ms_at((sprite.x + 20, sprite.y), moving=False, speed_smooth=0)
        drive(sprite, still_ms, frames=220)  # ~3.7s > 2.5s
        assert sprite.fsm.current_name == "idle"

    def test_playing_keeps_playing_when_mouse_moves(self):
        """鼠标持续在动 → 不会因静止走开（一直玩或追）。"""
        sprite = make_sprite()
        sprite.fsm.transition_to("playing")
        # 鼠标贴近且在动
        moving_ms = ms_at((sprite.x + 20, sprite.y), moving=True, speed_smooth=300)
        drive(sprite, moving_ms, frames=60)
        # 还在 playing 或 chasing（不会因"静止腻"回 idle）
        assert sprite.fsm.current_name in ("playing", "chasing")

    def test_cooldown_prevents_immediate_replay(self):
        """玩腻走开后，冷却期内鼠标仍在脚下也不立即回 playing。"""
        sprite = make_sprite()
        sprite.fsm.transition_to("playing")
        # 玩到腻走开
        still_ms = ms_at((sprite.x + 20, sprite.y), moving=False, speed_smooth=0)
        drive(sprite, still_ms, frames=220)
        assert sprite.fsm.current_name == "idle"
        # 冷却时间戳应被设到未来
        assert sprite.play_cooldown_until > time.monotonic()
        # 继续驱动，鼠标仍在脚下静止 → 不应回 playing
        drive(sprite, still_ms, frames=30)
        assert sprite.fsm.current_name == "idle"

    def test_cooldown_expires_allows_replay(self):
        """冷却过期后，鼠标在动时可重新进 playing。"""
        sprite = make_sprite()
        # 手动把冷却设到过去（模拟冷却已过）
        sprite.play_cooldown_until = time.monotonic() - 1.0
        sprite.fsm.transition_to("idle")
        # 鼠标贴近在动 → 应能进 playing（经 alert 或直接）
        moving_ms = ms_at((sprite.x + 20, sprite.y), moving=True, speed_smooth=300)
        drive(sprite, moving_ms, frames=10)
        # 应该离开了 idle（进 alert 或 playing）
        assert sprite.fsm.current_name != "idle"
