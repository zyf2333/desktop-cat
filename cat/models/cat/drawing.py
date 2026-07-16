"""猫的 QPainter 矢量绘制。

输入：已平移到猫中心的 painter、CatPose、facing、全局时间 t。
输出：绘制一只卡通橘猫。

绘制约定：
- 在 [-50, 50] x [-50, 50] 的逻辑坐标系里画（约 100 单位高），
  调用方（window）已把 painter.translate 到猫中心；本函数内部再缩放到 size。
- facing 通过水平镜像 painter 实现：facing=-1 时 scale(-1,1)。
- 所有参数都从 pose 取，缺失/越界会 clamp。
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)

from cat.models.cat.poses import CatPose
from cat.utils.geometry import clamp

if TYPE_CHECKING:
    pass

# ---- 配色（橘猫）----
COL_BODY = QColor("#F2A65A")        # 主体橙
COL_BODY_DARK = QColor("#D9842B")   # 阴影/条纹
COL_BELLY = QColor("#FBE3C8")       # 肚子米白
COL_INNER_EAR = QColor("#F4B8A8")   # 耳内粉
COL_NOSE = QColor("#E07A8B")        # 鼻头粉
COL_EYE = QColor("#3B7A57")         # 眼睛绿
COL_OUTLINE = QColor("#5A3A1B")     # 勾线深棕
COL_NOSE_OUT = QColor("#B85C6E")

# ---- 几何常量（逻辑单位）----
R = 50.0  # 缩放基准半径


def _outline_pen(width: float = 2.2) -> QPen:
    pen = QPen(COL_OUTLINE, width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def draw_cat(painter: QPainter, pose: CatPose, facing: int, t: float, size_px: int) -> None:
    """绘制一只猫。调用方已 translate 到猫中心。"""
    painter.save()
    # 整体缩放到目标尺寸（逻辑 2R → size_px）
    scale = size_px / (2 * R)
    painter.scale(scale, scale)
    # 朝向翻转
    if facing < 0:
        painter.scale(-1.0, 1.0)

    # 呼吸：极轻微的整体缩放
    breathe = 1.0 + 0.012 * math.sin(pose.breathe_phase)
    painter.scale(breathe, breathe)

    # 蓄力/拉伸：垂直压缩或拉长
    squash = 1.0 - 0.18 * clamp(pose.body_squash, 0.0, 1.0)
    stretch = 1.0 + 0.12 * clamp(pose.body_stretch, 0.0, 1.0)
    sy = squash * stretch
    sx = 1.0 / stretch * (1.0 + 0.06 * clamp(pose.body_squash, 0.0, 1.0))
    painter.scale(sx, sy)

    # 整体上抬（扑击跳起）
    painter.translate(0.0, -pose.body_lift)
    # 身体倾斜
    painter.rotate(math.degrees(pose.body_tilt))

    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(_outline_pen())

    # 绘制顺序：阴影 → 尾巴 → 后腿 → 身体 → 前腿 → 头 → 表情
    _draw_shadow(painter, pose)
    # wrestle 翻身：整体上下翻转（四脚朝天）
    if pose.on_back:
        painter.scale(1.0, -1.0)
    _draw_tail(painter, pose, t)
    _draw_hind_legs(painter, pose)
    _draw_body(painter, pose)
    _draw_front_legs(painter, pose)
    _draw_head(painter, pose, t)

    painter.restore()


def _draw_shadow(painter: QPainter, pose: CatPose) -> None:
    """宠物脚下的阴影（半透明扁椭圆），增强立体感。跳起时变淡变小。"""
    lift = clamp(pose.body_lift, 0.0, 60.0)
    # 跳得越高阴影越淡越小
    alpha = max(30, int(90 - lift * 1.2))
    rx = max(18.0, 30.0 - lift * 0.15)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(0, 0, 0, alpha))
    painter.drawEllipse(QPointF(0, 40), rx, 6.0)


# ---- 各部件 ----
def _draw_tail(painter: QPainter, pose: CatPose, t: float) -> None:
    """尾巴从身体右后侧伸出，做 S 形曲线，随 tail_wag 摆动。"""
    wag = math.sin(pose.tail_wag_phase) * pose.tail_wag
    base_angle = pose.tail_angle + wag * 0.6

    # 尾根位置（身体右下）
    root = QPointF(34, 18)
    # 用三段贝塞尔画 S 形
    length = 42
    tip_dir = base_angle
    c1 = QPointF(
        root.x() + math.cos(tip_dir - 0.6) * length * 0.5,
        root.y() - math.sin(tip_dir - 0.6) * length * 0.5 + wag * 8,
    )
    c2 = QPointF(
        root.x() + math.cos(tip_dir + 0.4) * length * 0.8,
        root.y() - math.sin(tip_dir + 0.4) * length * 0.8 + wag * 4,
    )
    tip = QPointF(
        root.x() + math.cos(tip_dir) * length,
        root.y() - math.sin(tip_dir) * length,
    )
    path = QPainterPath(root)
    path.cubicTo(c1, c2, tip)
    pen = _outline_pen(7.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.GlobalColor.transparent)
    painter.drawPath(path)
    # 尾尖深色
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(COL_BODY_DARK)
    painter.drawEllipse(tip, 5.5, 5.5)


def _draw_hind_legs(painter: QPainter, pose: CatPose) -> None:
    """后腿（两只小椭圆，在身体下方偏后）。"""
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(COL_BODY)
    # 后腿微动
    sway = math.sin(pose.leg_phase) * pose.leg_stride * 4
    painter.drawEllipse(QPointF(22, 34 + sway), 7, 9)
    painter.drawEllipse(QPointF(8, 34 - sway), 7, 9)
    # 爪子（米白）
    painter.setBrush(COL_BELLY)
    painter.drawEllipse(QPointF(22, 36 + sway), 5, 5)
    painter.drawEllipse(QPointF(8, 36 - sway), 5, 5)


def _draw_body(painter: QPainter, pose: CatPose) -> None:
    """椭圆身体 + 米白肚皮 + 橙色条纹。"""
    painter.setPen(_outline_pen())
    painter.setBrush(COL_BODY)
    # 主体椭圆
    painter.drawEllipse(QPointF(0, 12), 36, 26)
    # 肚子
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(COL_BELLY)
    painter.drawEllipse(QPointF(-2, 18), 24, 18)
    # 条纹（身体顶部几道深色短线）
    painter.setPen(QPen(COL_BODY_DARK, 2.4, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(-18, -4), QPointF(-12, -8))
    painter.drawLine(QPointF(-4, -10), QPointF(4, -10))
    painter.drawLine(QPointF(12, -8), QPointF(18, -4))


def _draw_front_legs(painter: QPainter, pose: CatPose) -> None:
    """前腿。舔毛时抬起一只爪子。"""
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(COL_BODY)
    if pose.grooming:
        # 一只前爪举到脸前
        painter.save()
        painter.translate(-6, 6)
        painter.rotate(-70)
        painter.drawEllipse(QPointF(0, 0), 5, 12)
        painter.setBrush(COL_BELLY)
        painter.drawEllipse(QPointF(0, 10), 5, 5)
        painter.restore()
        # 另一只前腿正常
        painter.setBrush(COL_BODY)
        painter.drawEllipse(QPointF(-18, 34), 6, 8)
        painter.setBrush(COL_BELLY)
        painter.drawEllipse(QPointF(-18, 36), 4.5, 4.5)
        return

    # swat 拍打：一只前爪高高抬起（paw_raise 0~1）
    paw_raise = clamp(getattr(pose, "paw_raise", 0.0), 0.0, 1.0)
    if paw_raise > 0.05:
        lift = paw_raise * 22  # 抬起高度
        painter.setBrush(COL_BODY)
        # 抬起的爪子（朝前上方）
        painter.save()
        painter.translate(2, 20 - lift)
        painter.rotate(-40 * paw_raise)
        painter.drawEllipse(QPointF(0, 0), 5, 11)
        painter.setBrush(COL_BELLY)
        painter.drawEllipse(QPointF(0, 9), 5, 5)
        painter.restore()
        # 另一只前腿正常
        painter.setBrush(COL_BODY)
        painter.drawEllipse(QPointF(-18, 34), 6, 8)
        painter.setBrush(COL_BELLY)
        painter.drawEllipse(QPointF(-18, 36), 4.5, 4.5)
        return

    sway = math.sin(pose.leg_phase + math.pi) * pose.leg_stride * 4
    painter.setBrush(COL_BODY)
    painter.drawEllipse(QPointF(-22, 34 + sway), 6, 8)
    painter.drawEllipse(QPointF(-12, 34 - sway), 6, 8)
    painter.setBrush(COL_BELLY)
    painter.drawEllipse(QPointF(-22, 36 + sway), 4.5, 4.5)
    painter.drawEllipse(QPointF(-12, 36 - sway), 4.5, 4.5)


def _draw_head(painter: QPainter, pose: CatPose, t: float) -> None:
    """头：圆脸 + 两耳 + 眼睛 + 鼻嘴。支持歪头/竖耳/困惑。"""
    # 头部位置（在身体上方），可上下浮动+左右转
    head_x = pose.head_turn * 6
    head_y = -22 + pose.head_bob
    painter.save()
    painter.translate(head_x, head_y)
    # 歪头（困惑时）：绕头中心旋转
    if abs(pose.head_tilt) > 1e-3:
        painter.rotate(math.degrees(pose.head_tilt))

    # 耳朵：ear_alert 越高耳朵越朝前竖（耳朵角度随 alert 变化）
    painter.setPen(_outline_pen())
    painter.setBrush(COL_BODY)
    # alert 影响耳朵顶端 y 坐标（更竖=更高更靠前）
    a = clamp(pose.ear_alert, 0.0, 1.0)
    ear_top_dy = -28 - a * 4        # 竖起时耳朵更高
    ear_top_dx = (1 - a) * 3        # 放松时耳朵略外八
    ear_l = QPolygonF([
        QPointF(-26, -6),
        QPointF(-20 - ear_top_dx, ear_top_dy),
        QPointF(-10, -12),
    ])
    ear_r = QPolygonF([
        QPointF(26, -6),
        QPointF(20 + ear_top_dx, ear_top_dy),
        QPointF(10, -12),
    ])
    painter.drawPolygon(ear_l)
    painter.drawPolygon(ear_r)
    # 耳内粉
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(COL_INNER_EAR)
    in_top_dy = ear_top_dy + 6
    in_l = QPolygonF([QPointF(-23, -8), QPointF(-19 - ear_top_dx, in_top_dy), QPointF(-13, -12)])
    in_r = QPolygonF([QPointF(23, -8), QPointF(19 + ear_top_dx, in_top_dy), QPointF(13, -12)])
    painter.drawPolygon(in_l)
    painter.drawPolygon(in_r)

    # 脸
    painter.setPen(_outline_pen())
    painter.setBrush(COL_BODY)
    painter.drawEllipse(QPointF(0, 0), 26, 24)

    # 脸颊米白（嘴部区域）
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(COL_BELLY)
    painter.drawEllipse(QPointF(0, 8), 16, 12)

    # 眼睛
    _draw_eyes(painter, pose)

    # 鼻子
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(COL_NOSE)
    painter.drawEllipse(QPointF(0, 6), 3.2, 2.4)
    # 嘴（根据 pose.mouth 选不同嘴形）
    _draw_mouth(painter, pose)

    # 胡须
    painter.setPen(QPen(COL_OUTLINE, 1.0))
    painter.drawLine(QPointF(-14, 6), QPointF(-24, 4))
    painter.drawLine(QPointF(-14, 9), QPointF(-24, 10))
    painter.drawLine(QPointF(14, 6), QPointF(24, 4))
    painter.drawLine(QPointF(14, 9), QPointF(24, 10))

    # 状态气泡：睡觉 Z / 困惑 ?
    _draw_status_bubble(painter, pose, t)

    painter.restore()


def _draw_mouth(painter: QPainter, pose: CatPose) -> None:
    """根据 pose.mouth 绘制不同嘴形：smile/open/lick/yawn。

    smile: 默认微笑（两道小弧）
    open:  张嘴（椭圆口腔，玩弄/兴奋时）
    lick:  舔舌（舌头伸出）
    yawn:  打哈欠（大椭圆）
    """
    pen = QPen(COL_OUTLINE, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    # 人中线（鼻到嘴的中点）
    painter.setPen(pen)
    painter.drawLine(QPointF(0, 8), QPointF(0, 11))

    mouth = getattr(pose, "mouth", "smile")
    if mouth == "open":
        # 张嘴：粉色口腔椭圆
        painter.setPen(pen)
        painter.setBrush(QColor("#E07A8B"))
        painter.drawEllipse(QPointF(0, 13), 4.5, 3.5)
    elif mouth == "lick":
        # 舔舌：嘴 + 粉色舌头下垂
        painter.setPen(pen)
        painter.setBrush(Qt.GlobalColor.transparent)
        painter.drawArc(QRectF(-6, 9, 6, 6), 0 * 16, 90 * 16)
        painter.drawArc(QRectF(0, 9, 6, 6), 90 * 16, 90 * 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#F4B8A8"))
        painter.drawEllipse(QPointF(0, 13), 2.5, 4.0)
    elif mouth == "yawn":
        # 打哈欠：大椭圆
        painter.setPen(pen)
        painter.setBrush(QColor("#7A3A4A"))
        painter.drawEllipse(QPointF(0, 13), 6, 7)
    else:
        # smile：默认两道小弧
        painter.setPen(pen)
        painter.setBrush(Qt.GlobalColor.transparent)
        painter.drawArc(QRectF(-6, 9, 6, 6), 0 * 16, 90 * 16)
        painter.drawArc(QRectF(0, 9, 6, 6), 90 * 16, 90 * 16)


def _draw_status_bubble(painter: QPainter, pose: CatPose, t: float) -> None:
    """在头顶绘制状态符号：睡觉 z / 困惑 ?。"""
    if pose.asleep:
        painter.setPen(QPen(COL_OUTLINE, 1.6))
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        zz = "z" * (1 + int(t * 1.5) % 3)
        painter.drawText(QRectF(16, -34, 24, 16), Qt.AlignmentFlag.AlignCenter, zz)
    elif pose.confused:
        # 困惑：头顶飘一个 "?"，带轻微浮动
        bob = math.sin(t * 3.0) * 2.0
        painter.setPen(QPen(QColor("#7A5CD6"), 2.0))
        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(-8, -42 + bob, 24, 20), Qt.AlignmentFlag.AlignCenter, "?")


def _draw_eyes(painter: QPainter, pose: CatPose) -> None:
    """眼睛：开合 + 瞳孔移动 + 瞳孔放大（兴奋）。

    pupil_dilate ∈ [0,1]：0=细缝瞳孔（放松），1=大圆瞳孔（兴奋/锁定）。
    真猫在兴奋/捕猎时瞳孔会显著放大变圆。
    """
    open_level = clamp(pose.eye_open * (1.0 - pose.blink), 0.0, 1.0)
    eye_dx = pose.pupil_dx * 2.0
    eye_dy = pose.pupil_dy * 1.5
    dilate = clamp(pose.pupil_dilate, 0.0, 1.0)

    if open_level <= 0.05 or pose.asleep:
        # 闭眼：画一道弧
        painter.setPen(QPen(COL_OUTLINE, 1.8, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.GlobalColor.transparent)
        painter.drawArc(QRectF(-14, -3, 8, 6), 0 * 16, 180 * 16)
        painter.drawArc(QRectF(6, -3, 8, 6), 0 * 16, 180 * 16)
        return

    # 睁眼：杏仁形眼眶
    eye_h = 9 * open_level
    painter.setPen(_outline_pen(1.8))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawEllipse(QPointF(-10, -2), 5, eye_h)
    painter.drawEllipse(QPointF(10, -2), 5, eye_h)
    # 瞳孔：dilate 越大瞳孔越宽越圆（兴奋），越小越细（放松，竖瞳）
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(COL_EYE)
    # 竖瞳宽度 1.4 → 圆瞳宽度 3.8；高度随 dilate 略减（变圆）
    pw = 1.4 + dilate * 2.4
    ph = eye_h * (0.75 - dilate * 0.15)
    painter.drawEllipse(QPointF(-10 + eye_dx, -2 + eye_dy), pw, ph)
    painter.drawEllipse(QPointF(10 + eye_dx, -2 + eye_dy), pw, ph)
    # 高光
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawEllipse(QPointF(-10 + eye_dx - 1, -2 + eye_dy - 2), 1.0, 1.0)
    painter.drawEllipse(QPointF(10 + eye_dx - 1, -2 + eye_dy - 2), 1.0, 1.0)
