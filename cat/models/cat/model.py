"""CatModel —— 猫模型的 Model 接口实现。

组装：提供默认姿态、绘制委托、专属状态机。
新增动作/状态在本模型的 actions/ 与 states/ 目录内完成，
本文件与主框架都不需要改动。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cat.core.model import Model
from cat.core.state_machine import StateMachine
from cat.models.cat.drawing import draw_cat
from cat.models.cat.poses import CatPose
from cat.models.cat.states import build_cat_state_machine

if TYPE_CHECKING:
    from PySide6.QtGui import QPainter

    from cat.core.pet_sprite import PetSprite


class CatModel(Model):
    name = "cat"

    def default_pose(self) -> CatPose:
        return CatPose()

    def draw(self, painter: "QPainter", pose: Any, facing: int, t: float, size_px: int) -> None:
        assert isinstance(pose, CatPose), "CatModel 只能绘制 CatPose"
        # 推进呼吸相位（用 t 做自驱动，无需外部更新）
        pose.breathe_phase = t * 1.6
        # 尾巴自摆（轻微）
        if pose.tail_wag > 0:
            pose.tail_wag_phase = t * 6.0
        draw_cat(painter, pose, facing, t, size_px=size_px)

    def create_state_machine(self, sprite: "PetSprite") -> StateMachine:
        return build_cat_state_machine(sprite)
