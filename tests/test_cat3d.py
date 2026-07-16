"""3D 猫模型的单元测试（rig 逻辑 + 模型接口，不需 GPU）。

Qt3D 的 mesh/entity 创建需要真实 GPU 上下文，无法离屏测试。
本测试聚焦：
- Cat3DModel 的接口契约（is_3d、advance、状态机）
- rig.update_rig 的纯计算逻辑（用 mock transform 验证调用）
"""
from __future__ import annotations

import math

from cat.core.model import get_model
from cat.core.pet_sprite import PetSprite
from cat.models.cat.poses import CatPose


class MockTransform:
    """模拟 QTransform，记录所有调用。"""

    def __init__(self):
        self.translation = None
        self.rotation = None
        self.scale = None
        self.scale3d = None
        self.calls = []

    def setTranslation(self, v): self.translation = v; self.calls.append(("trans", v))
    def setRotation(self, q): self.rotation = q; self.calls.append(("rot", q))
    def setRotationX(self, a): self.calls.append(("rotX", a))
    def setRotationY(self, a): self.calls.append(("rotY", a))
    def setRotationZ(self, a): self.calls.append(("rotZ", a))
    def setScale(self, s): self.scale = s; self.calls.append(("scale", s))
    def setScale3D(self, v): self.scale3d = v; self.calls.append(("scale3d", v))


class MockRig:
    """模拟 CatRig，持有 MockTransform。"""

    def __init__(self):
        self.root_transform = MockTransform()
        self.body_transform = MockTransform()
        self.head_transform = MockTransform()
        self.ear_L_transform = MockTransform()
        self.ear_R_transform = MockTransform()
        self.eye_L_transform = MockTransform()
        self.eye_R_transform = MockTransform()
        self.pupil_L_transform = MockTransform()
        self.pupil_R_transform = MockTransform()
        self.leg_transforms = [MockTransform() for _ in range(4)]
        self.tail_transforms = [MockTransform() for _ in range(3)]


class TestCat3DModelInterface:
    def test_model_registered_and_is_3d(self):
        m = get_model("cat3d")
        assert m.name == "cat3d"
        assert m.is_3d is True

    def test_default_pose_is_catpose(self):
        m = get_model("cat3d")
        pose = m.default_pose()
        assert isinstance(pose, CatPose)

    def test_advance_updates_breathe(self):
        """advance 应推进呼吸相位（复用 2D 逻辑）。"""
        m = get_model("cat3d")
        pose = CatPose()
        m.advance(pose, 1.0)
        assert pose.breathe_phase == 1.6  # t * 1.6

    def test_draw_raises_for_3d(self):
        """3D 模型的 draw 方法应报 NotImplementedError。"""
        m = get_model("cat3d")
        pose = CatPose()
        try:
            m.draw(None, pose, 1, 0.0, 96)
            assert False, "应抛 NotImplementedError"
        except NotImplementedError:
            pass

    def test_state_machine_builds(self):
        """3D 猫复用 2D 猫的状态机。"""
        m = get_model("cat3d")
        from cat import config
        sprite = PetSprite(get_model("cat3d"), x=100, y=100, size_px=96)
        fsm = sprite.fsm
        assert fsm.current_name == "idle"


class TestRigLogic:
    def test_update_rig_sets_root_rotation_by_facing(self):
        """facing +1 → root Y 旋转 0；-1 → 旋转 180。"""
        from cat.models.cat3d.rig import update_rig
        rig = MockRig()
        pose = CatPose()
        # facing 右
        update_rig(rig, pose, 1, 0.0)
        assert any(c[0] == "rotY" and c[1] == 0.0 for c in rig.root_transform.calls)
        # 重置后 facing 左
        rig.root_transform = MockTransform()
        update_rig(rig, pose, -1, 0.0)
        assert any(c[0] == "rotY" and c[1] == 180.0 for c in rig.root_transform.calls)

    def test_update_rig_applies_breathe_scale(self):
        """呼吸相位影响 root scale（应 >0）。"""
        from cat.models.cat3d.rig import update_rig
        rig = MockRig()
        pose = CatPose()
        pose.breathe_phase = 0.0
        update_rig(rig, pose, 1, 0.0)
        assert rig.root_transform.scale is not None
        assert 0.9 < rig.root_transform.scale < 1.1

    def test_update_rig_updates_all_legs(self):
        """4 条腿都应被设置 translation。"""
        from cat.models.cat3d.rig import update_rig
        rig = MockRig()
        pose = CatPose()
        pose.leg_stride = 0.5
        pose.leg_phase = 0.0
        update_rig(rig, pose, 1, 0.0)
        for leg_t in rig.leg_transforms:
            assert leg_t.translation is not None

    def test_update_rig_updates_tail_segments(self):
        """尾巴 3 段都应被设置 rotation。"""
        from cat.models.cat3d.rig import update_rig
        rig = MockRig()
        pose = CatPose()
        pose.tail_wag = 0.7
        update_rig(rig, pose, 1, 0.0)
        for seg_t in rig.tail_transforms:
            assert seg_t.rotation is not None

    def test_update_rig_squash_stretches_body(self):
        """body_squash 应改变 body 的 scale3d。"""
        from cat.models.cat3d.rig import update_rig
        rig = MockRig()
        pose = CatPose()
        update_rig(rig, pose, 1, 0.0)
        assert rig.body_transform.scale3d is not None
