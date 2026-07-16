"""3D 骨骼解算：把 CatPose 字段翻译成各部位 QTransform。

每帧调用 update_rig(rig, pose, facing, t)：
- root：位置（由窗口层设）、朝向（facing→Y轴旋转）、呼吸缩放
- body：squash/stretch/lift/tilt
- head：head_turn/head_bob/head_tilt
- 耳朵：ear_alert（竖起）
- 眼睛：blink（缩放）、瞳孔 dx/dy（平移）、dilate（缩放）
- 腿：leg_phase（摆动）
- 尾巴：tail_wag/phase（链式摆动）

坐标系见 builder.py 头注释。
"""
from __future__ import annotations

import math

from PySide6.QtGui import QQuaternion, QVector3D


def update_rig(rig, pose, facing: int, t: float, scale: float = 1.0) -> None:
    """根据 pose 更新 rig 各部位的 transform。

    Args:
        scale: 整体缩放系数（config.CAT3D_SCALE），乘到 root 的最终 scale。
    """
    # ===== root：朝向 + 呼吸 + 整体缩放 =====
    # facing +1 朝右(+X)，-1 朝左。猫默认面朝 +X，朝左绕 Y 转 180°。
    yaw = 0.0 if facing >= 0 else 180.0
    breathe = 1.0 + 0.02 * math.sin(pose.breathe_phase)
    rig.root_transform.setRotationY(yaw)
    # 呼吸 × 整体缩放（root 的 translation 由窗口层每帧设位置）
    rig.root_transform.setScale(breathe * scale)

    # ===== body：squash/stretch/lift/tilt =====
    squash = 1.0 - 0.18 * _clamp(pose.body_squash)
    stretch = 1.0 + 0.12 * _clamp(pose.body_stretch)
    # body 形变：Y 压扁、X 拉长
    rig.body_transform.setScale3D(QVector3D(1.0 / stretch * (1 + 0.06 * _clamp(pose.body_squash)),
                                             squash * stretch, 1.0))
    # body_lift → 上抬（translate Y）；body_tilt → 绕 Z 旋转
    body_y = _clamp(pose.body_lift) * 0.3
    rig.body_transform.setTranslation(QVector3D(0, body_y, 0))
    rig.body_transform.setRotationZ(math.degrees(pose.body_tilt))

    # ===== head：turn/bob/tilt =====
    # head_turn → 绕 Y 旋转（左右看）
    # head_bob → Y 平移
    # head_tilt → 绕 Z 旋转（歪头）
    head = rig.head_transform
    head.setTranslation(QVector3D(2.8, 0.8 + pose.head_bob * 0.05, 0))
    # 组合旋转：先 Y（turn）再 Z（tilt）
    qy = QQuaternion.fromAxisAndAngle(QVector3D(0, 1, 0), math.degrees(pose.head_turn * 0.6))
    qz = QQuaternion.fromAxisAndAngle(QVector3D(0, 0, 1), math.degrees(pose.head_tilt))
    head.setRotation(qy * qz)

    # ===== 耳朵：ear_alert（竖起 = 朝前并升高）=====
    ear_angle = -30.0 * _clamp(pose.ear_alert)  # 竖起时耳朵更垂直
    if rig.ear_L_transform is not None:
        rig.ear_L_transform.setRotation(QQuaternion.fromEulerAngles(-180, 0, 0))
        # 简化：用 scale 略升高度感
    if rig.ear_R_transform is not None:
        rig.ear_R_transform.setRotation(QQuaternion.fromEulerAngles(-180, 0, 0))

    # ===== 眼睛：blink（缩放 Y）、瞳孔平移、dilate（瞳孔缩放）=====
    eye_open = max(0.0, 1.0 - pose.blink) * (0.2 + 0.8 * pose.eye_open)
    eye_scale_y = max(0.05, eye_open)
    pdx = pose.pupil_dx * 0.15
    pdy = pose.pupil_dy * 0.1
    dilate = _clamp(pose.pupil_dilate)
    # 瞳孔：dilate 大→更圆（X 缩放变大）、更小→竖瞳（X 缩放小）
    pupil_scale_x = 0.4 + dilate * 0.9
    for eye_t, pupil_t in [(rig.eye_L_transform, rig.pupil_L_transform),
                            (rig.eye_R_transform, rig.pupil_R_transform)]:
        if eye_t is not None:
            eye_t.setScale3D(QVector3D(1.0, eye_scale_y, 1.0))
        if pupil_t is not None:
            pupil_t.setScale3D(QVector3D(pupil_scale_x, 1.0, 1.0))
            pupil_t.setTranslation(QVector3D(0.35 + pdx, pdy, 0))

    # ===== 腿：leg_phase 摆动（前后腿反相）=====
    stride = _clamp(pose.leg_stride)
    for i, leg_t in enumerate(rig.leg_transforms):
        phase = pose.leg_phase + (math.pi if i < 2 else 0)  # 前后反相
        sway = math.sin(phase) * stride * 0.5
        # 腿绕 X 轴小幅摆动（前后摆）
        base_x = [1.8, 1.8, -1.8, -1.8][i]
        base_z = [0.8, -0.8, 0.8, -0.8][i]
        leg_t.setTranslation(QVector3D(base_x, -1.8 + abs(sway) * 0.2, base_z))
        leg_t.setRotationX(math.degrees(sway))

    # ===== 尾巴：tail_wag + phase（链式摆动）=====
    wag = _clamp(pose.tail_wag)
    for i, seg_t in enumerate(rig.tail_transforms):
        swing = math.sin(pose.tail_wag_phase + i * 0.6) * wag * (0.3 + i * 0.1)
        # 每段绕 Z 旋转（左右甩），叠加基础倾斜
        seg_t.setRotation(QQuaternion.fromAxisAndAngle(QVector3D(0, 0, 1), 50 + math.degrees(swing)))


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))
