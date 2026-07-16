"""Cat3DModel —— 猫的 3D 渲染模型（low-poly）。

行为完全复用 2D 猫（同 CatPose、同状态机、同动作库），只是渲染走 Qt3D。
这验证了 pose 透传原则：换渲染层，状态机/动作零改动。

advance 复用 CatModel 的自驱动逻辑（呼吸/眨眼/摆尾）。
build_3d_scene 委托 builder.py 构建 entity 树。
render_3d 委托 rig.py 把 pose 翻译成 transform。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cat.core.model import Model
from cat.core.state_machine import StateMachine
from cat.models.cat.model import CatModel  # 复用其 advance 逻辑
from cat.models.cat.poses import CatPose
from cat.models.cat.states import build_cat_state_machine
from cat.models.cat3d.builder import build_cat
from cat.models.cat3d.rig import update_rig

if TYPE_CHECKING:
    from PySide6.QtGui import QPainter

    from cat.core.pet_sprite import PetSprite


class Cat3DModel(Model):
    name = "cat3d"
    is_3d = True

    def __init__(self) -> None:
        # 复用 2D CatModel 的 advance 逻辑（不重复实现呼吸/眨眼）
        self._2d = CatModel()
        self._rig = None  # build_3d_scene 后设置

    def default_pose(self) -> CatPose:
        return CatPose()

    def advance(self, pose: Any, t: float) -> None:
        """复用 2D 猫的自驱动（呼吸/眨眼/摆尾相位）。"""
        self._2d.advance(pose, t)

    def draw(self, painter: "QPainter", pose: Any, facing: int, t: float, size_px: int) -> None:
        raise NotImplementedError("Cat3DModel 是 3D 模型，不支持 2D draw")

    def build_3d_scene(self, root_entity: Any) -> Any:
        """构建 low-poly 猫的 entity 树，返回 rig 句柄。"""
        self._rig = build_cat(root_entity)
        return self._rig

    def render_3d(self, root_entity: Any, pose: Any, facing: int, t: float, scale: float) -> None:
        """每帧把 pose 翻译成 rig 各部位 transform。"""
        if self._rig is None:
            return
        update_rig(self._rig, pose, facing, t)

    def create_state_machine(self, sprite: "PetSprite") -> StateMachine:
        return build_cat_state_machine(sprite)
