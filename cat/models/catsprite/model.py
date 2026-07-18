"""CatSpriteModel —— 精灵序列帧渲染的猫模型（Desktop-Cat 素材）。

把状态机的 pose 翻译成"当前动画 + 帧索引 + 朝向"，用 QPainter 贴 PNG 帧。
行为完全复用 2D 猫（同状态机、同动作库），只是渲染从矢量换成贴图。

素材（Desktop-Cat，MIT 协议，72×64 像素风）：
- idle_01~04：待机（4 帧）
- walk_left_01~04 / walk_right_01~04：左右行走（各 4 帧，已分朝向）
- sleep_01~06：睡觉（6 帧）
- zzz_01~04：呼噜气泡（4 帧，叠加在 sleep 上）
- angry_01：生气（1 帧）

动作映射（pose → 动画 + 原始帧形变）：
- asleep → zzz（素材本身已包含睡猫和 Z，只绘制一次）
- 移动（leg_stride 大）→ walk_left / walk_right（按 facing 选，不翻转素材）
- 扑击（body_lift/stretch 高）→ walk 原始帧 + 横向拉伸/腾空
- 玩弄（playing）→ idle 原始帧 + 摇摆/翻滚/拍击
- 警觉/困惑 → idle 原始帧 + 绷紧/歪头

复杂动作只形变原素材，脸、鼻子、项圈和像素轮廓不会在切换时突变。
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, List

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


def _pose_to_anim(pose: CatPose, facing: int) -> str:
    """根据 pose 和 facing 决定播放哪个精灵动画。

    素材已分左右朝向，直接按 facing 选 walk_left/walk_right，不做镜像翻转。
    """
    # 睡觉
    if pose.asleep:
        return "zzz"
    # 困惑沿用待机原帧，由绘制层负责歪头和摇晃。
    if pose.confused:
        return "idle"
    # 扑击/跳扑（空中或拉伸）——暂用 walk 代替（缺 pounce 素材）
    # 扑的位移由 pose.body_lift/stretch 驱动，视觉上仍能看到跳起
    if pose.body_lift > 5 or pose.body_stretch > 0.5:
        # 扑的时候用 walk（快速帧），加上 body_lift 的位置变化体现跳跃
        return "walk_right" if facing >= 0 else "walk_left"
    # 蓄力（pounce windup：压低+警觉）——暂用 idle
    if pose.body_squash > 0.4 and pose.pupil_dilate > 0.7:
        return "idle"
    # 爪拍使用由原始 idle 帧制作的专用序列，不再运行时外挂胳膊。
    if pose.paw_raise > 0.1:
        return "swat_right" if facing >= 0 else "swat_left"
    # 其他玩弄继续复用待机原帧，避免 angry 自带符号突兀。
    if pose.on_back:
        return "idle"
    # 发现鼠标/悬停警觉：保持同一张脸，由形变表现突然绷紧。
    if pose.alerted or pose.ear_alert > 0.65:
        return "idle"
    # 移动中（走/跑/潜行/追逐）——按朝向选左右行走
    if pose.leg_stride > 0.2:
        return "walk_right" if facing >= 0 else "walk_left"
    # 默认待机（含坐/舔毛/伸懒腰/警觉/困惑）
    return "idle"


class CatSpriteModel(Model):
    name = "catsprite"

    def __init__(self) -> None:
        self._2d = CatModel()  # 复用 advance（呼吸/眨眼）
        self._frame_t = 0.0    # 动画帧计时器
        self._last_anim = None
        self._frames: List[QPixmap] = []
        self._frame_idx = 0
        self._fps = 8          # 精灵动画帧率（Desktop-Cat 风格偏慢更可爱）
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
        anim = _pose_to_anim(pose, facing)
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
        if anim.startswith("swat_"):
            # 与 SwatAction 的抬爪进度同步，抬起和收回都会逐帧变化。
            idx = min(len(frames) - 1, int(max(0.0, min(1.0, pose.paw_raise)) * len(frames)))
        else:
            idx = self._frame_idx % len(frames)
        pm = frames[idx]

        # 缩放到 size_px（72x64 → 等比放大，宽度对齐 size_px）
        # 用 NEAREST 缩放保持像素风锐利（不用 Smooth 避免模糊）
        scale = size_px / pm.width()
        w = int(pm.width() * scale)
        h = int(pm.height() * scale)
        scaled = pm.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio,
                           Qt.TransformationMode.FastTransformation)

        # 素材已分朝向，不需要镜像翻转
        painter.save()
        # 复杂动作只形变原始帧，确保角色身份和像素细节完全连贯。
        breathe = 1.0 + 0.015 * math.sin(pose.breathe_phase)
        squash_amount = max(0.0, min(1.0, pose.body_squash))
        stretch_amount = max(0.0, min(1.0, pose.body_stretch))
        # 蓄力时压低；扑出时沿行进方向拉长。
        sx = 1.0 + 0.18 * stretch_amount + 0.05 * squash_amount
        sy = breathe * (1.0 - 0.14 * squash_amount - 0.07 * stretch_amount)
        if pose.alerted and not pose.on_back:
            sx *= 1.0 + 0.015 * math.sin(t * 16.0)
            sy *= 1.025
        if pose.on_back:
            # 扭打表现为趴低、弹动，不再把整张猫图旋转九十度。
            sx *= 1.08 + 0.03 * math.sin(t * 10.0)
            sy *= 0.76 + 0.04 * math.sin(t * 12.0)
        # 居中绘制（猫脚在底部中心，所以 x 居中、y 底部对齐）
        # body_lift 让整张图上移（扑击跳起）
        lift = max(0.0, min(60.0, pose.body_lift)) * scale * 0.5
        # 只做小幅水平晃动；不再旋转整张图，避免猫身体突然歪倒。
        confused_shift = math.sin(t * 9.0) * 3.0 if pose.confused else 0.0
        action_shift = max(-0.15, min(0.15, pose.body_tilt)) * w * 0.22
        alert_lift = 2.5 if pose.alerted and pose.body_lift <= 0 else 0.0
        painter.translate(confused_shift + action_shift, -lift - alert_lift)
        painter.scale(sx, sy)
        painter.drawPixmap(QPointF(-w / 2, -h / 2), scaled)

        painter.restore()

    def create_state_machine(self, sprite: "PetSprite") -> StateMachine:
        return build_cat_state_machine(sprite)
