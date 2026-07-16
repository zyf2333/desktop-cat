"""动作层共享的小工具。

独立成模块，避免 actions/__init__ 与各动作文件之间的循环导入。
"""
from __future__ import annotations


def reset_to_stand(pose) -> None:
    """把 pose 重置为标准站立姿态。动作开始/结束时调用以清理上次残留。"""
    pose.eye_open = 1.0
    pose.pupil_dx = 0.0
    pose.pupil_dy = 0.0
    pose.blink = 0.0
    pose.body_squash = 0.0
    pose.body_stretch = 0.0
    pose.body_lift = 0.0
    pose.body_tilt = 0.0
    pose.tail_wag = 0.3
    pose.leg_stride = 0.0
    pose.head_turn = 0.0
    pose.head_bob = 0.0
    pose.asleep = False
    pose.grooming = False
    pose.ear_alert = 0.0
    pose.head_tilt = 0.0
    pose.pupil_dilate = 0.0
    pose.confused = False
    pose.alerted = False
