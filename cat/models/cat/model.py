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
    is_3d = False  # 2D QPainter 渲染

    def default_pose(self) -> CatPose:
        return CatPose()

    def advance(self, pose: Any, t: float) -> None:
        """推进渲染无关的自驱动状态（呼吸/眨眼/摆尾）。2D/3D 共用。"""
        assert isinstance(pose, CatPose)
        # 呼吸相位
        pose.breathe_phase = t * 1.6
        # 尾巴自摆
        if pose.tail_wag > 0:
            pose.tail_wag_phase = t * 6.0
        # 自动眨眼：每 ~4 秒一次（仅当动作未主动设 blink 时）
        blink_cycle = t % 4.2
        if 4.0 < blink_cycle < 4.18:
            local = (blink_cycle - 4.0) / 0.18
            auto_blink = 1.0 - abs(local * 2 - 1)
        else:
            auto_blink = 0.0
        if pose.blink < 0.1:
            pose.blink = auto_blink

    def draw(self, painter: "QPainter", pose: Any, facing: int, t: float, size_px: int) -> None:
        assert isinstance(pose, CatPose), "CatModel 只能绘制 CatPose"
        draw_cat(painter, pose, facing, t, size_px=size_px)

    def create_state_machine(self, sprite: "PetSprite") -> StateMachine:
        return build_cat_state_machine(sprite)
