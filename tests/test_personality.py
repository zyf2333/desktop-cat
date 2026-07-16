"""个性系统的单元测试。"""
from __future__ import annotations

from cat.core.personality import Personality


def test_defaults():
    p = Personality()
    assert 0.0 <= p.liveliness <= 1.0
    assert 0.0 <= p.alertness <= 1.0


def test_clamp_caps_values():
    p = Personality(liveliness=2.0, alertness=-1.0, patience=0.5, playfulness=1.5, curiosity=0)
    c = p.clamp()
    assert c.liveliness == 1.0
    assert c.alertness == 0.0
    assert c.patience == 0.5
    assert c.playfulness == 1.0
    assert c.curiosity == 0.0


def test_pet_sprite_has_personality():
    """PetSprite 默认从 config 注入个性。"""
    from cat import config
    from cat.core.model import get_model
    from cat.core.pet_sprite import PetSprite
    s = PetSprite(get_model("cat"), x=0, y=0, size_px=96)
    assert isinstance(s.personality, Personality)
    assert s.personality.liveliness == config.PERSONALITY["liveliness"]


def test_pet_sprite_custom_personality():
    from cat.core.model import get_model
    from cat.core.pet_sprite import PetSprite
    p = Personality(liveliness=1.0, alertness=0.1)
    s = PetSprite(get_model("cat"), x=0, y=0, size_px=96, personality=p)
    assert s.personality.liveliness == 1.0
    assert s.personality.alertness == 0.1
