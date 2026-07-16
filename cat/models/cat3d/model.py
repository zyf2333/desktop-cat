"""Cat3DModel —— 猫的 3D 渲染模型。

优先加载 assets/models/ 下的现成精致模型（.glb）；
找不到则回退到 low-poly 几何体拼装（builder.py）。

行为完全复用 2D 猫（同 CatPose、同状态机、同动作库），只是渲染走 Qt3D。
这验证了 pose 透传原则：换渲染层，状态机/动作零改动。
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from cat import config
from cat.core.model import Model
from cat.core.state_machine import StateMachine
from cat.models.cat.model import CatModel  # 复用其 advance 逻辑
from cat.models.cat.poses import CatPose
from cat.models.cat.states import build_cat_state_machine
from cat.models.cat3d.builder import build_cat
from cat.models.cat3d.mesh_loader import find_cat_model, load_mesh, models_dir
from cat.models.cat3d.rig import update_rig

if TYPE_CHECKING:
    from PySide6.Qt3DCore import Qt3DCore
    from PySide6.QtGui import QPainter

    from cat.core.pet_sprite import PetSprite


class Cat3DModel(Model):
    name = "cat3d"
    is_3d = True

    def __init__(self) -> None:
        # 复用 2D CatModel 的 advance 逻辑（不重复实现呼吸/眨眼）
        self._2d = CatModel()
        self._rig = None          # low-poly 模式用
        self._mesh_transform = None  # 外部模型模式用
        self._use_external = False

    def default_pose(self) -> CatPose:
        return CatPose()

    def advance(self, pose: Any, t: float) -> None:
        """复用 2D 猫的自驱动（呼吸/眨眼/摆尾相位）。"""
        self._2d.advance(pose, t)

    def draw(self, painter: "QPainter", pose: Any, facing: int, t: float, size_px: int) -> None:
        raise NotImplementedError("Cat3DModel 是 3D 模型，不支持 2D draw")

    def build_3d_scene(self, root_entity: Any) -> Any:
        """构建猫的 3D 场景：优先加载外部模型，回退 low-poly。"""
        model_path = find_cat_model()
        if model_path is not None:
            print(f"[cat3d] 加载外部模型: {model_path}")
            self._build_from_mesh(root_entity, model_path)
            self._use_external = True
        else:
            print(f"[cat3d] 未找到外部模型（放 .glb 到 {models_dir()}），回退 low-poly")
            self._rig = build_cat(root_entity)
            self._use_external = False
        return self._rig

    def _build_from_mesh(self, root_entity: Any, model_path: str) -> None:
        """加载外部 glb/gltf/obj 模型。"""
        mesh = load_mesh(root_entity, model_path)
        self._mesh_transform = __import__("PySide6.Qt3DCore", fromlist=["Qt3DCore"]).Qt3DCore.QTransform(root_entity)
        # 包装到一个 entity
        entity = __import__("PySide6.Qt3DCore", fromlist=["Qt3DCore"]).Qt3DCore.QEntity(root_entity)
        entity.addComponent(mesh)
        entity.addComponent(self._mesh_transform)

    def render_3d(self, root_entity: Any, pose: Any, facing: int, t: float, scale: float) -> None:
        """每帧更新渲染。外部模型用整体 transform；low-poly 用 rig。"""
        if self._use_external:
            self._render_external(pose, facing, t, scale)
        elif self._rig is not None:
            update_rig(self._rig, pose, facing, t, scale=scale)

    def _render_external(self, pose: Any, facing: int, t: float, scale: float) -> None:
        """外部模型：整体 transform（朝向 + 呼吸 + squash/stretch + 位置由窗口设）。"""
        if self._mesh_transform is None:
            return
        from PySide6.QtGui import QQuaternion, QVector3D
        # facing → Y 轴旋转
        yaw = 0.0 if facing >= 0 else 180.0
        # 呼吸缩放
        breathe = 1.0 + 0.02 * math.sin(pose.breathe_phase)
        # squash/stretch（垂直形变）
        squash = 1.0 - 0.18 * max(0.0, min(1.0, pose.body_squash))
        stretch = 1.0 + 0.12 * max(0.0, min(1.0, pose.body_stretch))
        body_lift = max(0.0, min(60.0, pose.body_lift)) * 0.3
        self._mesh_transform.setScale3D(
            QVector3D(scale * breathe / stretch, scale * breathe * squash * stretch, scale * breathe)
        )
        self._mesh_transform.setTranslation(QVector3D(0, body_lift, 0))
        self._mesh_transform.setRotation(
            QQuaternion.fromAxisAndAngle(QVector3D(0, 1, 0), yaw)
            * QQuaternion.fromAxisAndAngle(QVector3D(0, 0, 1), math.degrees(pose.body_tilt))
        )

    def create_state_machine(self, sprite: "PetSprite") -> StateMachine:
        return build_cat_state_machine(sprite)
