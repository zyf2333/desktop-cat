"""二维决策（_intents）的单元测试。"""
from __future__ import annotations

from cat import config
from cat.core.model import get_model
from cat.core.personality import Personality
from cat.core.pet_sprite import PetSprite
from cat.models.cat.states._intents import Intent, decide_intent
from cat.mouse_tracker import MouseState


def make_sprite(x=0.0, y=0.0, personality=None):
    return PetSprite(get_model("cat"), x=x, y=y, size_px=96, personality=personality)


def ms(pos, **kw):
    d = dict(speed_smooth=400.0, is_escaping=False, still_seconds=0.0, moving=True)
    d.update(kw)
    return MouseState(pos=pos, **d)


class TestDecideIntent:
    def test_no_mouse_returns_ignore(self):
        s = make_sprite(0, 0)
        assert decide_intent(s, None) == Intent.IGNORE

    def test_far_away_lost(self):
        """超出关注范围（lose_r≈420）→ LOST。"""
        s = make_sprite(0, 0)
        assert decide_intent(s, ms((1000, 0))) == Intent.LOST

    def test_far_escaping_is_lost(self):
        s = make_sprite(0, 0)
        assert decide_intent(s, ms((2000, 0), is_escaping=True)) == Intent.LOST

    def test_medium_far_slow_still_ignored(self):
        """中等距离（警觉范围外、关注范围内）且鼠标不动 → IGNORE。"""
        s = make_sprite(0, 0)
        # alert_r≈220，350 在 lose_r(420) 内但在 alert_r 外，鼠标静止
        assert decide_intent(s, ms((350, 0), moving=False, speed_smooth=0)) == Intent.IGNORE

    def test_very_close_is_play(self):
        s = make_sprite(0, 0)
        # 进入 PLAY_DIST（60）内
        assert decide_intent(s, ms((30, 0))) == Intent.PLAY

    def test_close_and_fast_is_pounce(self):
        s = make_sprite(0, 0)
        # 在 POUNCE_DIST（90）内且速度快
        assert decide_intent(s, ms((75, 0), speed_smooth=1000)) == Intent.POUNCE

    def test_slow_mouse_in_alert_range_is_stalk(self):
        s = make_sprite(0, 0)
        # 在警觉范围内，鼠标慢
        assert decide_intent(s, ms((150, 0), speed_smooth=50)) == Intent.STALK

    def test_fast_mouse_in_alert_range_is_chase(self):
        s = make_sprite(0, 0)
        # 在警觉范围内，鼠标快
        assert decide_intent(s, ms((150, 0), speed_smooth=500)) == Intent.CHASE


class TestPersonalityInfluence:
    def test_high_alertness_extends_range(self):
        """高警觉度的猫，更远的鼠标也能引起 STALK（在 alert_r 内）；
        低警觉猫的 alert_r 小，同样距离会落到 ALERT（外缘）。"""
        s_alert = make_sprite(personality=Personality(alertness=1.0))
        s_calm = make_sprite(personality=Personality(alertness=0.0))
        # 距离 250，慢速
        far_mouse = ms((250, 0), speed_smooth=50)
        # 高警觉猫的 alert_r ≈ 220*(0.7+0.6)=286，250 在内 → STALK
        assert decide_intent(s_alert, far_mouse) == Intent.STALK
        # 低警觉猫的 alert_r ≈ 220*0.7=154，250 超出 alert_r 但在 lose_r 内 → ALERT
        assert decide_intent(s_calm, far_mouse) == Intent.ALERT

    def test_patient_cat_stalks_faster_mice(self):
        """高耐心猫对更快的目标仍愿潜行（stalk_speed 阈值更高）。"""
        s_patient = make_sprite(personality=Personality(patience=1.0))
        s_impatient = make_sprite(personality=Personality(patience=0.0))
        mid_mouse = ms((150, 0), speed_smooth=140)
        # 高耐心 stalk_speed ≈ 120*(0.8+0.4)=144，140 < 144 → STALK
        assert decide_intent(s_patient, mid_mouse) == Intent.STALK
        # 低耐心 stalk_speed ≈ 120*0.8=96，140 > 96 → CHASE
        assert decide_intent(s_impatient, mid_mouse) == Intent.CHASE
