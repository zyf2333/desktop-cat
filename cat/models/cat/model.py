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
        # 自动眨眼：每 ~4 秒眨一次（仅当动作未主动设 blink 时）
        # 用周期函数：blink_phase 在每个周期开头有短暂峰值
        blink_cycle = t % 4.2
        if 4.0 < blink_cycle < 4.18:
            # 眨眼持续约 0.18s，三角形包络
            local = (blink_cycle - 4.0) / 0.18
            auto_blink = 1.0 - abs(local * 2 - 1)
        else:
            auto_blink = 0.0
        # 只在动作没有主动设 blink（blink==0）时叠加自动眨眼
        if pose.blink < 0.1:
            pose.blink = auto_blink
        draw_cat(painter, pose, facing, t, size_px=size_px)

    def create_state_machine(self, sprite: "PetSprite") -> StateMachine:
        return build_cat_state_machine(sprite)
