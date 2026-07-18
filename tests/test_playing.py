"""PLAYING 状态的单元测试 + play 族动作验证。"""
from __future__ import annotations

import random

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


def drive(sprite, mouse_state, frames=60, dt=1/60):
    for _ in range(frames):
        sprite.update(dt, mouse_state)


class TestPlayActions:
    def test_make_action_play_returns_one_of_four_variants(self):
        from cat.models.cat.actions import make_action
        sprite = make_sprite()
        seen = set()
        for _ in range(50):
            a = make_action("play", sprite=sprite, target=lambda: (0, 0))
            seen.add(a.name)
        # 应该能看到多种 play 变体被选中
        assert seen.issubset({"swat", "jump_pounce", "wrestle", "sniff"})
        assert len(seen) >= 2  # 至少两种

    def test_swat_finishes_after_swats(self):
        """直接驱动 SwatAction（不经 fsm），验证按时结束。"""
        from cat.models.cat.actions.swat import SwatAction
        sprite = make_sprite(0, 0)
        swat = SwatAction(target=(50, 0), swats=2)
        swat.start(sprite)
        for i in range(120):
            swat.update(sprite, 1 / 60)
            if swat.is_done():
                break
        assert swat.is_done()

    def test_jump_pounce_finishes(self):
        from cat.models.cat.actions.jump_pounce import JumpPounceAction
        sprite = make_sprite(0, 0)
        jp = JumpPounceAction(target=(50, 0))
        jp.start(sprite)
        for i in range(50):
            jp.update(sprite, 1 / 60)
            if jp.is_done():
                break
        assert jp.is_done()

    def test_wrestle_finishes(self):
        from cat.models.cat.actions.wrestle import WrestleAction
        sprite = make_sprite(0, 0)
        w = WrestleAction(target=(0, 0), duration=0.5)
        w.start(sprite)
        for i in range(40):
            w.update(sprite, 1 / 60)
            if w.is_done():
                break
        assert w.is_done()

    def test_sniff_finishes(self):
        from cat.models.cat.actions.sniff import SniffAction
        sprite = make_sprite(0, 0)
        sn = SniffAction(target=(40, 0), duration=0.5)
        sn.start(sprite)
        for i in range(40):
            sn.update(sprite, 1 / 60)
            if sn.is_done():
                break
        assert sn.is_done()


class TestPlayingState:
    def test_playing_transitions_to_confused_on_lost(self):
        """PLAYING 中鼠标丢失 → confused。"""
        sprite = make_sprite()
        # 先进入 playing（直接 transition_to）
        sprite.fsm.transition_to("playing")
        assert sprite.fsm.current_name == "playing"
        # 鼠标跑远
        drive(sprite, ms_at((sprite.x + 1000, sprite.y)), frames=10)
        assert sprite.fsm.current_name == "confused"

    def test_playing_transitions_to_chasing_on_mouse_escape(self):
        """PLAYING 中鼠标逃开但还在视野 → chasing。"""
        sprite = make_sprite()
        sprite.fsm.transition_to("playing")
        # 鼠标移到中等距离（PLAY_DIST*2.5=150 之外，但 LOSE_RADIUS 内）且在动
        drive(sprite, ms_at((sprite.x + 200, sprite.y), speed_smooth=600), frames=5)
        assert sprite.fsm.current_name == "chasing"

    def test_playing_eventually_returns_to_idle(self):
        """玩够轮数后回 idle（鼠标静止）。"""
        sprite = make_sprite()
        sprite.fsm.transition_to("playing")
        # 鼠标贴着猫但静止（让 playing 动作播完后 mouse_state.moving=False）
        # 注意：playing 动作播完会 _after_play，达到 max_rounds 后回 idle
        # 这里只验证首次正常退出，避免回到自主生活后的随机状态影响断言。
        ms_still = ms_at((sprite.x + 20, sprite.y), moving=False, speed_smooth=0)
        for _ in range(400):
            sprite.update(1 / 60, ms_still)
            if sprite.fsm.current_name != "playing":
                break
        assert sprite.fsm.current_name == "idle"


class TestClickInteraction:
    def test_sprite_contains_inside_hit_radius(self):
        sprite = make_sprite(100, 100)
        assert sprite.contains(100, 100) is True  # 中心
        assert sprite.contains(100 + 30, 100) is True  # 半径内

    def test_sprite_contains_outside_hit_radius(self):
        sprite = make_sprite(100, 100)
        assert sprite.contains(100 + 200, 100) is False  # 远超半径

    def test_on_click_transitions_to_confused(self):
        sprite = make_sprite(100, 100)
        sprite.on_click(200, 100)
        assert sprite.facing == 1  # 朝向点击来源（右侧）
        assert sprite.fsm.current_name == "confused"
