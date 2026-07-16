"""low-poly 猫的 3D 骨骼层级构建。

用 Qt3DExtras 基本几何体（球/柱/锥/胶囊）拼出一只卡通猫。
关键是建立 QEntity 父子层级（骨骼），每帧由 rig.py 更新各部位的 QTransform。

骨骼层级：
  root (位置/朝向Y/scale)
  └─ body (squash/stretch/lift/tilt)
     ├─ head (head_turn/head_bob/head_tilt)
     │  ├─ ear_L, ear_R
     │  ├─ eye_L, eye_R (含瞳孔)
     │  └─ nose
     ├─ leg_FL, leg_FR, leg_BL, leg_BR (leg_phase 摆动)
     └─ tail_seg_0..N (链式摆动)

所有尺寸用"逻辑单位"，由 root 的 scale 统一缩放到世界坐标。
"""
from __future__ import annotations

import math

from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.QtGui import QColor, QMatrix4x4, QQuaternion, QVector3D

# ---- 配色（与 2D 橘猫一致）----
COL_BODY = QColor("#F2A65A")
COL_BODY_DARK = QColor("#D9842B")
COL_BELLY = QColor("#FBE3C8")
COL_INNER_EAR = QColor("#F4B8A8")
COL_NOSE = QColor("#E07A8B")
COL_EYE_WHITE = QColor("#FFFFFF")
COL_EYE = QColor("#3B7A57")
COL_OUTLINE = QColor("#5A3A1B")


class CatRig:
    """猫的 3D 骨骼句柄。持有各部位的 QTransform 引用，供 rig 更新。"""

    def __init__(self) -> None:
        # root 层
        self.root_transform: Qt3DCore.QTransform = None
        # body 层
        self.body_transform: Qt3DCore.QTransform = None
        # head 层
        self.head_transform: Qt3DCore.QTransform = None
        self.ear_L_transform: Qt3DCore.QTransform = None
        self.ear_R_transform: Qt3DCore.QTransform = None
        self.eye_L_transform: Qt3DCore.QTransform = None
        self.eye_R_transform: Qt3DCore.QTransform = None
        self.pupil_L_transform: Qt3DCore.QTransform = None
        self.pupil_R_transform: Qt3DCore.QTransform = None
        # 腿（前左/前右/后左/后右）
        self.leg_transforms = []  # list[QTransform]
        # 尾巴段
        self.tail_transforms = []  # list[QTransform]


def _make_entity(parent, mesh=None, material=None, transform=None) -> Qt3DCore.QEntity:
    """创建一个带组件的 entity。"""
    e = Qt3DCore.QEntity(parent)
    if mesh is not None:
        e.addComponent(mesh)
    if material is not None:
        e.addComponent(material)
    if transform is not None:
        e.addComponent(transform)
    return e


def _make_material(parent, color: QColor, alpha: float = 1.0) -> Qt3DExtras.QPhongAlphaMaterial:
    mat = Qt3DExtras.QPhongAlphaMaterial(parent)
    mat.setDiffuse(color)
    # ambient 比 diffuse 略暗
    amb = QColor(color)
    h, s, v, a = amb.getHsl()
    amb.setHsl(h, s, max(0, int(v * 0.6)), a)
    mat.setAmbient(amb)
    mat.setSpecular(QColor("#FFE9C8"))
    mat.setShininess(40.0)
    mat.setAlpha(alpha)
    return mat


def build_cat(root_parent: Qt3DCore.QEntity) -> CatRig:
    """在 root_parent 下构建一只 low-poly 猫，返回 rig 句柄。

    坐标系约定（逻辑单位）：
    - X 轴：左右（猫面朝 +X 时为正面）
    - Y 轴：上下（+Y 上）
    - Z 轴：前后（+Z 朝向相机/玩家，即猫的正面朝 +Z）
    猫尺寸约 10 单位高。
    """
    rig = CatRig()

    # ===== root 层 =====
    rig.root_transform = Qt3DCore.QTransform()
    root_entity = _make_entity(root_parent, transform=rig.root_transform)

    # ===== body 层 =====
    rig.body_transform = Qt3DCore.QTransform()
    body_entity = _make_entity(root_entity, transform=rig.body_transform)

    # 身体：用椭球（拉长的球）代替胶囊（QCapsuleMesh 在此 PySide6 版本不可用）
    body_mesh = Qt3DExtras.QSphereMesh(body_entity)
    body_mesh.setRadius(2.0)
    body_mesh.setRings(16)
    body_mesh.setSlices(16)
    # 用 scale 拉长成椭球（沿 X 横躺）
    body_rot = Qt3DCore.QTransform()
    body_rot.setScale3D(QVector3D(1.8, 1.2, 1.3))  # 横向拉长成身体
    body_inner = _make_entity(
        body_entity,
        mesh=body_mesh,
        material=_make_material(body_entity, COL_BODY),
        transform=body_rot,
    )

    # 肚子：稍亮的椭球贴在底部（简化：一个稍小的胶囊）
    belly_mesh = Qt3DExtras.QSphereMesh(body_entity)
    belly_mesh.setRadius(1.6)
    belly_transform = Qt3DCore.QTransform()
    belly_transform.setTranslation(QVector3D(0, -0.3, 0.3))
    belly_transform.setScale3D(QVector3D(2.0, 1.2, 1.0))
    _make_entity(body_entity, mesh=belly_mesh,
                 material=_make_material(body_entity, COL_BELLY),
                 transform=belly_transform)

    # ===== 4 条腿 =====
    leg_positions = [
        QVector3D(1.8, -1.8, 0.8),   # 前左
        QVector3D(1.8, -1.8, -0.8),  # 前右
        QVector3D(-1.8, -1.8, 0.8),  # 后左
        QVector3D(-1.8, -1.8, -0.8), # 后右
    ]
    for i, pos in enumerate(leg_positions):
        leg_mesh = Qt3DExtras.QCylinderMesh(body_entity)
        leg_mesh.setRadius(0.45)
        leg_mesh.setLength(2.0)
        leg_transform = Qt3DCore.QTransform()
        leg_transform.setTranslation(pos)
        # 圆柱默认沿 Y，腿朝下不需旋转
        leg_entity = _make_entity(
            body_entity,
            mesh=leg_mesh,
            material=_make_material(body_entity, COL_BODY),
            transform=leg_transform,
        )
        rig.leg_transforms.append(leg_transform)
        # 爪子（稍亮的小球在腿底）
        paw_mesh = Qt3DExtras.QSphereMesh(leg_entity)
        paw_mesh.setRadius(0.5)
        paw_transform = Qt3DCore.QTransform()
        paw_transform.setTranslation(QVector3D(0, -1.1, 0))
        _make_entity(leg_entity, mesh=paw_mesh,
                     material=_make_material(leg_entity, COL_BELLY),
                     transform=paw_transform)

    # ===== 尾巴（3 段链）=====
    prev_parent = body_entity
    tail_base = QVector3D(-2.5, 0.5, 0)  # 尾根
    tail_offset = QVector3D(-0.9, 0.7, 0)  # 每段相对上一段的偏移
    for i in range(3):
        seg_mesh = Qt3DExtras.QCylinderMesh(prev_parent)
        seg_mesh.setRadius(0.4 - i * 0.08)
        seg_mesh.setLength(1.2)
        seg_transform = Qt3DCore.QTransform()
        seg_transform.setTranslation(tail_offset)
        # 圆柱沿 Y，尾巴斜向上，旋转使其指向斜后上
        seg_transform.setRotation(QQuaternion.fromAxisAndAngle(QVector3D(0, 0, 1), 50))
        seg_entity = _make_entity(
            prev_parent,
            mesh=seg_mesh,
            material=_make_material(prev_parent, COL_BODY),
            transform=seg_transform,
        )
        rig.tail_transforms.append(seg_transform)
        prev_parent = seg_entity

    # ===== head 层 =====
    rig.head_transform = Qt3DCore.QTransform()
    rig.head_transform.setTranslation(QVector3D(2.8, 0.8, 0))
    head_entity = _make_entity(body_entity, transform=rig.head_transform)

    # 头：球
    head_mesh = Qt3DExtras.QSphereMesh(head_entity)
    head_mesh.setRadius(1.9)
    head_mesh.setRings(16)
    head_mesh.setSlices(16)
    _make_entity(head_entity, mesh=head_mesh,
                 material=_make_material(head_entity, COL_BODY))

    # 耳朵：两个锥
    for side, x_off, sign in [("L", 0.9, 1), ("R", 0.9, -1)]:
        ear_mesh = Qt3DExtras.QConeMesh(head_entity)
        ear_mesh.setTopRadius(0.0)
        ear_mesh.setBottomRadius(0.7)
        ear_mesh.setLength(1.3)
        ear_mesh.setRings(8)
        ear_mesh.setSlices(8)
        ear_transform = Qt3DCore.QTransform()
        ear_transform.setTranslation(QVector3D(0.3, 1.7, sign * 0.9))
        ear_transform.setRotationX(-180)  # 锥尖朝上
        ear_entity = _make_entity(head_entity, mesh=ear_mesh,
                                   material=_make_material(head_entity, COL_BODY),
                                   transform=ear_transform)
        if sign > 0:
            rig.ear_L_transform = ear_transform
        else:
            rig.ear_R_transform = ear_transform
        # 耳内粉（小一点的锥）
        inner_mesh = Qt3DExtras.QConeMesh(ear_entity)
        inner_mesh.setTopRadius(0.0)
        inner_mesh.setBottomRadius(0.4)
        inner_mesh.setLength(0.9)
        inner_transform = Qt3DCore.QTransform()
        inner_transform.setTranslation(QVector3D(0, 0.1, 0))
        inner_transform.setRotationZ(180)
        _make_entity(ear_entity, mesh=inner_mesh,
                     material=_make_material(ear_entity, COL_INNER_EAR, alpha=0.9),
                     transform=inner_transform)

    # 眼睛（白球 + 绿瞳孔）
    for sign, attr_eye, attr_pupil in [(1, "eye_L_transform", "pupil_L_transform"),
                                        (-1, "eye_R_transform", "pupil_R_transform")]:
        eye_mesh = Qt3DExtras.QSphereMesh(head_entity)
        eye_mesh.setRadius(0.45)
        eye_transform = Qt3DCore.QTransform()
        eye_transform.setTranslation(QVector3D(0.9, 0.2, sign * 0.8))
        eye_entity = _make_entity(head_entity, mesh=eye_mesh,
                                   material=_make_material(head_entity, COL_EYE_WHITE),
                                   transform=eye_transform)
        setattr(rig, attr_eye, eye_transform)
        # 瞳孔
        pupil_mesh = Qt3DExtras.QSphereMesh(eye_entity)
        pupil_mesh.setRadius(0.22)
        pupil_transform = Qt3DCore.QTransform()
        pupil_transform.setTranslation(QVector3D(0.35, 0, 0))  # 略前凸
        pupil_transform.setScale3D(QVector3D(0.4, 1.0, 1.0))  # 竖瞳
        _make_entity(eye_entity, mesh=pupil_mesh,
                     material=_make_material(eye_entity, COL_EYE),
                     transform=pupil_transform)
        setattr(rig, attr_pupil, pupil_transform)

    # 鼻子：粉色小球
    nose_mesh = Qt3DExtras.QSphereMesh(head_entity)
    nose_mesh.setRadius(0.25)
    nose_transform = Qt3DCore.QTransform()
    nose_transform.setTranslation(QVector3D(1.75, -0.3, 0))
    _make_entity(head_entity, mesh=nose_mesh,
                 material=_make_material(head_entity, COL_NOSE),
                 transform=nose_transform)

    return rig
