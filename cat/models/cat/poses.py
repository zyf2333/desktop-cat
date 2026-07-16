"""猫的姿态（pose）定义。

pose 是模型自定义的不透明对象，框架不解析。这里定义猫的所有可动画参数。

设计思路：用一个可变 dataclass 承载所有关节/表情参数，
Action 通过修改这些字段来驱动动画，drawing.py 据此绘制。
这样新增动作 = 修改 pose 字段 + 在 drawing 里支持，互不侵入。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CatPose:
    """猫的完整姿态参数。

    坐标系：以猫的几何中心为原点，单位是"逻辑像素"
    （drawing 会按 size_px 做整体缩放）。
    大部分字段是有界量，约定取值范围见注释；drawing 内部会 clamp。

    身体朝向由 sprite.facing 决定（+1/-1），不在 pose 内。
    """

    # ---- 眼睛 ----
    eye_open: float = 1.0           # 0=闭眼, 1=全睁
    pupil_dx: float = 0.0           # 瞳孔水平偏移（看向哪边），[-1,1]
    pupil_dy: float = 0.0           # 瞳孔垂直偏移，[-1,1]
    blink: float = 0.0              # 眨眼进度，0=睁, 1=闭（与 eye_open 叠加）

    # ---- 身体姿态 ----
    body_squash: float = 0.0        # 身体压缩（蓄力/落地）：0=正常, 1=压扁
    body_stretch: float = 0.0       # 身体拉伸（跳跃中）：0=正常, 1=拉长
    body_lift: float = 0.0          # 整体上抬（离地高度），像素，用于扑击跳起
    body_tilt: float = 0.0          # 身体倾斜（弧度），正值=头朝上

    # ---- 尾巴 ----
    tail_angle: float = 0.0         # 尾巴根部相对竖直方向的角度（弧度）
    tail_wag: float = 0.0           # 尾巴摆动幅度，0=不动
    tail_wag_phase: float = 0.0     # 尾巴摆动相位，持续累加

    # ---- 腿 ----
    leg_phase: float = 0.0          # 走/跑的腿摆相位，持续累加
    leg_stride: float = 0.0         # 腿摆动幅度，0=并拢，1=大步

    # ---- 头部 ----
    head_turn: float = 0.0          # 头部水平转动（看向哪边），[-1,1]
    head_bob: float = 0.0           # 头部上下浮动，像素

    # ---- 状态标记（影响绘制分支，由 Action 设置）----
    asleep: bool = False            # 睡觉：闭眼+Z
    grooming: bool = False          # 舔毛：前爪抬起+头低下

    # ---- 捕猎/情绪标记 ----
    ear_alert: float = 0.0          # 耳朵竖起程度 [0,1]：警觉时耳朵朝前竖
    head_tilt: float = 0.0          # 头部歪斜（弧度）：困惑时歪头
    pupil_dilate: float = 0.0       # 瞳孔放大 [0,1]：兴奋/锁定时放大
    confused: bool = False          # 困惑：问号 + 歪头 + 眨眼
    alerted: bool = False           # 警觉态：身体微紧、瞳孔追踪

    # ---- 周期动画自驱动（drawing 用，由 model 维护）----
    breathe_phase: float = 0.0      # 呼吸相位
