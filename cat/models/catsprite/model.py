"""CatSpriteModel —— 精灵序列帧渲染的猫模型。

把状态机的 pose 翻译成"当前动画 + 帧索引 + 朝向"，用 QPainter 贴 PNG 帧。
行为完全复用 2D 猫（同状态机、同动作库），只是渲染从矢量换成贴图。

pose → 动画映射规则（在 _pose_to_anim 里）：
- 走/跑/潜行/追逐类 → walk 动画
- 扑击/跳扑 → jump 动画
- 玩弄（swat 等）→ attack 动画（cat_a1）
- 其他（待机/坐/睡/舔毛）→ idle 动画

朝向：素材朝左，facing=+1（右）时翻转。
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, List, Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPixmap

from cat import config
from cat.core.model import Model
from cat.core.state_machine import StateMachine
from cat.models.cat.model import CatModel  # 复用 advance
from cat.models.cat.poses import CatPose
from cat.models.cat.states import build_cat_state_machine
from cat.models.catsprite.sprite_loader import get_animation, load_all

if TYPE_CHECKING:
    from cat.core.pet_sprite import PetSprite


# pose 状态 → 精灵动画名映射（纯靠 pose 字段判断，不依赖 fsm_state）
def _pose_to_anim(pose: CatPose) -> str:
    """根据 pose 决定播放哪个精灵动画。

    判断优先级（从高到低）：
    1. 睡觉（asleep）→ cat_die（倒地图当躺睡）
    2. 扑击中（body_lift 高 或 stretch 高）→ cat_jump
    3. 蓄力（squash 高 + 不在地面）→ cat_jump
    4. 困惑（confused 标记）→ cat_idle
    5. 移动中（leg_stride 大）→ cat_walk
    6. 默认 → cat_idle
    """
    # 睡觉
    if pose.asleep:
        return "cat_die"
    # 扑击/跳扑（空中 或 拉伸）
    if pose.body_lift > 5 or pose.body_stretch > 0.5:
        return "cat_jump"
    # 蓄力（pounce windup：压低 + 警觉）
    if pose.body_squash > 0.4 and pose.pupil_dilate > 0.7:
        return "cat_jump"
    # 移动中（走/跑/潜行/追逐都靠 leg_stride）
    if pose.leg_stride > 0.2:
        return "cat_walk"
    # 默认待机（含坐/舔毛/伸懒腰/警觉/困惑）
    return "cat_idle"


class CatSpriteModel(Model):
    name = "catsprite"
    is_3d = False  # 走 2D QPainter 渲染（贴图）

    def __init__(self) -> None:
        self._2d = CatModel()  # 复用 advance（呼吸/眨眼）
        self._frame_t = 0.0    # 动画帧计时器
        self._last_anim = None
        self._frames: List[QPixmap] = []
        self._frame_idx = 0
        self._fps = 10         # 精灵动画帧率
        self._loaded = False

    def default_pose(self) -> CatPose:
        return CatPose()

    def advance(self, pose: Any, t: float) -> None:
        self._2d.advance(pose, t)
        # 推进精灵帧
        self._frame_t += 1.0 / config.RENDER_FPS
        if self._frame_t >= 1.0 / self._fps:
            self._frame_t = 0.0
            self._frame_idx += 1

    def draw(self, painter: QPainter, pose: Any, facing: int, t: float, size_px: int) -> None:
        assert isinstance(pose, CatPose)
        if not self._loaded:
            load_all()
            self._loaded = True

        # 根据 pose 决定当前动画
        anim = _pose_to_anim(pose)
        frames = get_animation(anim)
        if anim != self._last_anim:
            # 切换动画，重置帧索引
            self._last_anim = anim
            self._frames = frames
            self._frame_idx = 0
            self._frame_t = 0.0
        if not frames:
            return

        # 帧索引循环
        idx = self._frame_idx % len(frames)
        pm = frames[idx]

        # 缩放到 size_px（保持长宽比，50x50 → size_px）
        scale = size_px / max(pm.width(), pm.height())
        w = int(pm.width() * scale)
        h = int(pm.height() * scale)

        # 朝向翻转：素材朝左，facing=+1（右）需镜像
        painter.save()
        if facing >= 0:
            painter.translate(w / 2, 0)
            painter.scale(-1, 1)
            painter.translate(-w / 2, 0)
        # 呼吸微缩放
        breathe = 1.0 + 0.01 * math.sin(pose.breathe_phase)
        # squash/stretch
        squash = 1.0 - 0.15 * max(0.0, min(1.0, pose.body_squash))
        painter.scale(1.0, squash * breathe)
        # 居中绘制（猫脚在底部中心）
        painter.drawPixmap(QPointF(-w / 2, -h / 2), pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                                                              Qt.TransformationMode.SmoothTransformation))
        painter.restore()

    def create_state_machine(self, sprite: "PetSprite") -> StateMachine:
        return build_cat_state_machine(sprite)
