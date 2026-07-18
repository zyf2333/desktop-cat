"""像素猫动作映射必须始终复用原始素材组。"""
from cat.models.cat.poses import CatPose
from cat.models.catsprite.model import _pose_to_anim


def test_alert_uses_original_idle_sprite():
    pose = CatPose(alerted=True, ear_alert=1.0)
    assert _pose_to_anim(pose, 1) == "idle"


def test_confused_uses_original_idle_sprite():
    pose = CatPose(confused=True)
    assert _pose_to_anim(pose, 1) == "idle"


def test_pounce_reuses_directional_walk_frames():
    pose = CatPose(body_lift=20, body_stretch=0.8)
    assert _pose_to_anim(pose, 1) == "walk_right"
    assert _pose_to_anim(pose, -1) == "walk_left"


def test_regular_motion_keeps_directional_walk_frames():
    pose = CatPose(leg_stride=0.7)
    assert _pose_to_anim(pose, 1) == "walk_right"
    assert _pose_to_anim(pose, -1) == "walk_left"


def test_swat_uses_dedicated_directional_frames():
    pose = CatPose(paw_raise=0.8)
    assert _pose_to_anim(pose, 1) == "swat_right"
    assert _pose_to_anim(pose, -1) == "swat_left"


def test_sleep_uses_single_complete_zzz_frame():
    pose = CatPose(asleep=True)
    assert _pose_to_anim(pose, 1) == "zzz"
