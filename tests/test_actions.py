"""动作层单元测试。

用 FakeSprite 验证动作的开始/推进/完成，不依赖 Qt 或真实绘制。
重点测：WalkAction 到达后结束、PounceAction 三阶段推进与完成、
SitAction 计时结束、reset_to_stand 清理字段。
"""
from __future__ import annotations

import math

from cat import config
from cat.models.cat.actions import ACTIONS, reset_to_stand
from cat.models.cat.actions.pounce import PounceAction
from cat.models.cat.actions.walk import WalkAction
from cat.models.cat.poses import CatPose


class FakeFsm:
    """记录 transition_to 调用，不驱动真实状态。"""

    def __init__(self, sprite):
        self.sprite = sprite
        self.transitioned_to = None

    def transition_to(self, name):
        self.transitioned_to = name
        return True


class FakeSprite:
    """复刻 PetSprite 的动作相关接口，但脱离 Qt/模型。"""

    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
        self.facing = 1
        self.pose = CatPose()
        self.mouse_state = None
        self._action = None
        self.fsm = FakeFsm(self)

    def play(self, action, on_done=None):
        action.on_done = on_done
        self._action = action
        action.start(self)

    @property
    def has_action(self):
        return self._action is not None

    def clear_action(self):
        self._action = None


def test_reset_to_stand_clears_pose():
    pose = CatPose()
    pose.body_squash = 0.8
    pose.asleep = True
    pose.grooming = True
    pose.pupil_dx = 0.5
    reset_to_stand(pose)
    assert pose.body_squash == 0.0
    assert pose.asleep is False
    assert pose.grooming is False
    assert pose.pupil_dx == 0.0


def test_walk_reaches_target_and_finishes():
    sprite = FakeSprite(x=0.0, y=0.0)
    walk = WalkAction((100.0, 0.0), speed_px_s=200.0)
    done_flag = []
    sprite.play(walk, on_done=lambda: done_flag.append(True))
    assert walk.is_done() is False
    # 多帧推进：每帧 0.05s，速度 200 → 每帧 10px，10 帧到 100
    for _ in range(20):
        sprite._action.update(sprite, 0.05)
        if walk.is_done():
            break
    assert walk.is_done() is True
    assert done_flag == [True]
    assert math.isclose(sprite.x, 100.0, abs_tol=0.5)


def test_walk_facing_follows_target_direction():
    sprite = FakeSprite(x=0.0, y=0.0)
    walk = WalkAction((-50.0, 0.0), speed_px_s=100.0)
    sprite.play(walk)
    sprite._action.update(sprite, 0.05)
    # 目标在左侧 → facing 应为 -1
    assert sprite.facing == -1


def test_pounce_goes_through_phases_and_finishes():
    sprite = FakeSprite(x=0.0, y=0.0)
    pounce = PounceAction((80.0, 0.0))
    done_flag = []
    sprite.play(pounce, on_done=lambda: done_flag.append(True))

    # 验证初始进入 windup，身体开始压低
    assert pounce._phase == PounceAction.PHASE_WINDUP

    # 推过 windup 阶段
    windup = config.POUNCE_WINDUP_S
    sprite._action.update(sprite, windup + 0.01)
    assert pounce._phase == PounceAction.PHASE_LUNGE

    # 推过冲刺阶段（冲刺时间 ≈ 距离/速度）
    lunge_time = 80.0 / config.POUNCE_SPEED_PX_S
    sprite._action.update(sprite, lunge_time + 0.01)
    assert pounce._phase == PounceAction.PHASE_RECOVER

    # 推过 recover 阶段（0.18s）
    sprite._action.update(sprite, 0.19)
    assert pounce.is_done() is True
    assert done_flag == [True]
    # 最终位置应在目标附近
    assert math.isclose(sprite.x, 80.0, abs_tol=1.0)


def test_pounce_clamps_max_distance():
    """目标太远时，扑击距离不超过 POUNCE_MAX_DIST_PX。"""
    sprite = FakeSprite(x=0.0, y=0.0)
    pounce = PounceAction((9999.0, 0.0))
    sprite.play(pounce)
    # 锁定后的目标应被 clamp
    assert pounce._target[0] <= config.POUNCE_MAX_DIST_PX + 0.1


def test_pounce_facing_locks_to_target():
    sprite = FakeSprite(x=0.0, y=0.0)
    sprite.facing = 1
    pounce = PounceAction((-50.0, 0.0))
    sprite.play(pounce)
    assert sprite.facing == -1  # 朝向左侧目标


def test_sit_finishes_after_duration():
    sprite = FakeSprite(x=0.0, y=0.0)
    sit = ACTIONS["sit"](duration=1.0)
    sprite.play(sit)
    # 推进到 duration 之后
    sprite._action.update(sprite, 1.01)
    assert sit.is_done() is True


def test_actions_registry_has_core_actions():
    for name in ["walk", "run", "pounce", "sit", "sleep", "groom", "stretch"]:
        assert name in ACTIONS
