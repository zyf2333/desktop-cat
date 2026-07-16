"""集中配置。所有可调参数都在这里，调手感时只改本文件。

约定：本模块不依赖任何 Qt 对象，纯常量，便于 import 与测试。
"""
from __future__ import annotations

# ---- 模型 ----
MODEL_NAME = "cat"  # 当前使用的模型；--model 启动参数会覆盖此值

# ---- 鼠标追踪 ----
MOUSE_POLL_HZ = 60                # 鼠标采样频率（Hz）
ESCAPE_SPEED_PX_S = 2500          # 甩脱判定速度阈值（px/s）
ESCAPE_DURATION_S = 0.3           # 超阈值持续多久才判定甩脱（秒）
MOUSE_STILL_THRESHOLD_PX_S = 30   # 速度低于此值视为"静止"
MOUSE_SMOOTH_WINDOW_S = 0.3       # 速度滑动平均窗口（秒）

# ---- 追逐行为 ----
CHASE_SPEED_PX_S = 350            # 追逐速度
CHASE_SLOWDOWN_DIST_PX = 40       # 距离小于此值时减速靠近，避免抖动

# ---- 扑击行为 ----
POUNCE_TRIGGER_DIST_PX = 80       # 进入此距离可能触发扑击
POUNCE_PROBABILITY = 0.015        # 在扑击距离内、每帧触发扑击的概率
POUNCE_WINDUP_S = 0.18            # 扑击前蓄力（压低身体）时间
POUNCE_SPEED_PX_S = 1200          # 扑击冲刺速度
POUNCE_MAX_DIST_PX = 250          # 扑击最大冲刺距离
POUNCE_REACH_DIST_PX = 12         # 冲刺到离目标多近算扑到

# ---- 渲染 ----
RENDER_FPS = 60
PET_SIZE_PX = 96                  # 宠物渲染尺寸（模型无关）

# ---- 空闲行为（IDLE）----
IDLE_WANDER_RADIUS_PX = 60        # IDLE 游走半径（围绕"家"点）
IDLE_WANDER_SPEED_PX_S = 80       # IDLE 游走速度
IDLE_ACTION_INTERVAL_S = (3, 8)   # 每隔 N 秒随机一个空闲小动作
IDLE_SLEEP_AFTER_S = 45           # 鼠标静止超过 N 秒进入 SLEEPING

# ---- 调试 ----
DEBUG = False                     # True 时绘制猫的锚点/状态名等辅助信息
