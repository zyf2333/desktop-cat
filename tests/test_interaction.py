"""悬停、拖拽和自主生活行为测试。"""
from __future__ import annotations

from cat import config
from cat.core.model import get_model
from cat.core.pet_sprite import PetSprite
from cat.mouse_tracker import MouseState


def make_sprite(x=500.0, y=500.0):
    sprite = PetSprite(get_model("cat"), x=x, y=y, size_px=config.PET_SIZE_PX)
    sprite.world_bounds = (0.0, 0.0, 1000.0, 800.0)
    return sprite


def mouse_at(pos, **kw):
    values = dict(speed_smooth=300.0, is_escaping=False,
                  still_seconds=0.0, moving=True)
    values.update(kw)
    return MouseState(pos=pos, **values)


class TestHover:
    def test_hover_immediately_alerts(self):
        sprite = make_sprite()
        sprite.on_hover(sprite.x + 10, sprite.y)
        assert sprite.is_hovered is True
        assert sprite.fsm.current_name == "alert"
        assert sprite.pose.ear_alert == 1.0

    def test_repeated_hover_does_not_restart_state(self):
        sprite = make_sprite()
        sprite.on_hover(sprite.x + 10, sprite.y)
        action = sprite.current_action
        sprite.on_hover(sprite.x + 5, sprite.y)
        assert sprite.current_action is action


class TestDrag:
    def test_drag_moves_sprite_and_pauses_fsm(self):
        sprite = make_sprite()
        sprite.begin_drag()
        sprite.drag_to(700, 620)
        before = (sprite.x, sprite.y)
        sprite.update(1.0, mouse_at((900, 700)))
        assert (sprite.x, sprite.y) == before
        assert before == (700, 620)

    def test_drag_is_clamped_to_screen_and_release_reacts(self):
        sprite = make_sprite()
        sprite.begin_drag()
        sprite.drag_to(-1000, 5000)
        assert sprite.x > 0
        assert sprite.y < 800
        sprite.end_drag()
        assert sprite.is_dragging is False
        assert sprite.fsm.current_name == "confused"


class TestAutonomousLife:
    def test_autonomous_round_can_trigger_pooping(self, monkeypatch):
        import cat.models.cat.states.idle_state as idle_module
        sprite = make_sprite()
        state = sprite.fsm.get("idle")
        monkeypatch.setattr(idle_module.random, "random", lambda: 0.0)
        state._start_autonomous_activity(sprite)
        assert sprite.current_action is not None
        assert sprite.current_action.name == "poop"

    def test_zoomies_move_without_mouse_target(self):
        sprite = make_sprite()
        state = sprite.fsm.get("idle")
        start = (sprite.x, sprite.y)
        state._zoomies_remaining = 1
        state._continue_zoomies(sprite)
        far_mouse = mouse_at((5000, 5000), moving=False, speed_smooth=0)
        for _ in range(30):
            sprite.update(1 / 60, far_mouse)
        assert (sprite.x, sprite.y) != start
        assert sprite.current_action is not None

    def test_far_mouse_motion_does_not_wake_sleeping_cat(self):
        sprite = make_sprite()
        sprite.fsm.transition_to("sleeping")
        sprite.update(1 / 60, mouse_at((5000, 5000)))
        assert sprite.fsm.current_name == "sleeping"

    def test_near_mouse_motion_wakes_into_alert(self):
        sprite = make_sprite()
        sprite.fsm.transition_to("sleeping")
        sprite.update(1 / 60, mouse_at((sprite.x + 80, sprite.y)))
        assert sprite.fsm.current_name == "alert"

    def test_cat_eventually_sleeps_even_if_far_mouse_keeps_moving(self):
        sprite = make_sprite()
        sprite.sleep_after_seconds = 0.01
        sprite.update(0.02, mouse_at((5000, 5000)))
        assert sprite.fsm.current_name == "sleeping"

    def test_grooming_does_not_reset_sleepiness(self):
        sprite = make_sprite()
        sprite.awake_seconds = 12.0
        sprite.fsm.transition_to("grooming")
        sprite.fsm.transition_to("idle")
        assert sprite.awake_seconds == 12.0

    def test_dropping_persists_until_clicked(self):
        from cat.models.cat.actions.poop import Dropping
        sprite = make_sprite()
        dropping = Dropping(100, 100, 8)
        sprite.droppings.append(dropping)
        sprite.update(999, mouse_at((5000, 5000), moving=False, speed_smooth=0))
        assert sprite.droppings == [dropping]
        assert sprite.remove_dropping_at(100, 96) is True
        assert sprite.droppings == []

    def test_click_outside_dropping_keeps_it(self):
        from cat.models.cat.actions.poop import Dropping
        sprite = make_sprite()
        dropping = Dropping(100, 100, 8)
        sprite.droppings.append(dropping)
        assert sprite.remove_dropping_at(300, 300) is False
        assert sprite.droppings == [dropping]
