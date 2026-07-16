"""集中配置。所有可调参数都在这里，调手感时只改本文件。

约定：本模块不依赖任何 Qt 对象，纯常量，便于 import 与测试。
"""
from __future__ import annotations

# ---- 模型 ----
MODEL_NAME = "cat"  # 当前使用的模型；--model 启动参数会覆盖此值
                    # "cat" = 2D 矢量猫；"cat3d" = 3D low-poly 猫（Qt3D）

# ---- 3D 渲染（仅 is_3d 模型用）----
RENDER_MODE = "auto"          # "auto"=按模型 is_3d 选；"2d"=强制 2D；"3d"=强制 3D
CAMERA_DISTANCE = 22.0        # 3D 相机距猫的距离（世界单位）
CAT3D_SCALE = 1.0             # 3D 猫的整体缩放（应用到 root transform）
CAMERA_ORTHO_HALF = 8.0       # 正交投影半高（猫高约7-10单位，此值越小猫越大）
CAMERA_YAW = -25.0            # 相机水平偏角（度），略侧视露出身体长度
CAMERA_PITCH = -8.0           # 相机俯角（度），略俯视露出腿
ENABLE_3D_LIGHTING = True     # 3D 光照开关

# ---- 鼠标追踪 ----
MOUSE_POLL_HZ = 60                # 鼠标采样频率（Hz）
ESCAPE_SPEED_PX_S = 2500          # 甩脱判定速度阈值（px/s）
ESCAPE_DURATION_S = 0.3           # 超阈值持续多久才判定甩脱（秒）
MOUSE_STILL_THRESHOLD_PX_S = 30   # 速度低于此值视为"静止"
MOUSE_SMOOTH_WINDOW_S = 0.3       # 速度滑动平均窗口（秒）

# ---- 关注范围（捕猎行为总开关）----
ALERT_RADIUS_PX = 220             # 鼠标进入此半径且移动 → 猫警觉
LOSE_RADIUS_PX = 420              # 鼠标移出此半径（且在追/警觉中）→ 猫困惑、放弃

# ---- 二维决策阈值（距离 × 速度 → 意图）----
PLAY_DIST_PX = 60                 # 此距离内 → 可能进入 PLAYING（玩弄）
POUNCE_DIST_PX = 90               # 此距离内 + 鼠标快 → 直接扑
STALK_MOUSE_SPEED_PX_S = 120      # 鼠标速度低于此 → 倾向潜行（慢目标好潜行）
POUNCE_MOUSE_SPEED_PX_S = 800     # 鼠标速度高于此 + 近距离 → 倾向直接扑（快目标要果断）
CHASE_TO_PLAY_PROB = 0.008        # 追逐中进入玩距的每帧转 PLAYING 概率
STALK_TO_PLAY_PROB = 0.012        # 潜行中进入玩距的每帧转 PLAYING 概率

# ---- 警觉 → 发现 ----
ALERT_DURATION_S = (0.4, 0.8)     # 警觉持续时间（随机），之后转入发现
NOTICE_DURATION_S = (0.3, 0.6)    # 发现持续时间，之后开始潜行/追

# ---- 潜行（缓慢接近）----
STALK_SPEED_PX_S = 90             # 潜行速度（很慢很轻）
STALK_END_DIST_PX = 70            # 潜行到此距离 → 进入扑击蓄力
STALK_GIVEUP_S = 4.0              # 潜行超过这么久还没靠近 → 转追逐

# ---- 追逐（玩耍感）----
CHASE_SPEED_PX_S = 350            # 追逐基准速度
CHASE_SPEED_JITTER = 0.4          # 速度随机波动幅度（占基准的比例，0.4=±40%）
CHASE_PAUSE_PROBABILITY = 0.004   # 每帧触发"停顿盯着"的概率
CHASE_PAUSE_DURATION_S = (0.2, 0.5)  # 停顿时长
CHASE_SLOWDOWN_DIST_PX = 40       # 距离小于此值时减速靠近，避免抖动
CHASE_TO_POUNCE_DIST_PX = 80      # 追逐中进入此距离 → 可能转扑击蓄力
CHASE_TO_POUNCE_PROB = 0.01       # 追逐中转扑击的每帧概率

# ---- 扑击行为 ----
POUNCE_TRIGGER_DIST_PX = 80       # 进入此距离可能触发扑击（兼容旧逻辑）
POUNCE_PROBABILITY = 0.015        # 每帧触发扑击的概率（兼容旧逻辑）
POUNCE_WINDUP_S = 0.18            # 扑击前蓄力（压低身体）时间
POUNCE_SPEED_PX_S = 1200          # 扑击冲刺速度
POUNCE_MAX_DIST_PX = 250          # 扑击最大冲刺距离
POUNCE_REACH_DIST_PX = 12         # 冲刺到离目标多近算扑到

# ---- 困惑（找不到鼠标）----
CONFUSED_DURATION_S = (1.2, 2.2)  # 困惑持续时长（四处张望后回 idle）

# ---- 玩腻（PLAYING 中鼠标静止）----
# 鼠标不动超过此秒数 → 猫觉得没意思，主动走开。
# 受个性 patience 影响：有耐心的猫撑更久（0→0.5x，1→1.6x）。
PLAY_BORED_AFTER_S = 2.5

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

# ---- 个性（默认值，启动时注入 PetSprite；多宠物可各给不同实例）----
# 用 dict 而非直接 import Personality，避免 config 依赖 core（保持 config 纯常量）。
PERSONALITY = {
    "liveliness": 0.7,    # 活泼度
    "alertness": 0.5,     # 警觉度
    "patience": 0.6,      # 耐心
    "playfulness": 0.6,   # 玩心
    "curiosity": 0.5,     # 好奇心
}
