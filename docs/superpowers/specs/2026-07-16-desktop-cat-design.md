# 桌面宠物猫 · 设计文档（第一版）

- **日期**：2026-07-16
- **状态**：已与用户逐节确认，待最终评审
- **目标平台**：macOS（第一版），架构需便于未来跨平台支持 Windows

## 1. 目标与范围

### 1.1 一句话目标
在 macOS 桌面上养一只矢量绘制的宠物猫，它会追着鼠标跑；鼠标快速甩动时它会放弃追逐；靠近鼠标时有概率突然扑过去。

### 1.2 第一版范围（IN-SCOPE）
- 透明、无边框、始终置顶的桌面窗口，点击穿透（纯观赏，不响应点击）。
- 全桌面 2D 自由移动（不限于屏幕底部）。
- 行为：追鼠标、被甩脱后放弃、靠近时概率扑击。
- 丰富的空闲状态：溜达、坐、舔毛、伸懒腰、睡觉。
- 矢量绘制（QPainter）的卡通猫，左右翻转朝向。
- 可插拔的**模型抽象层**：未来可替换为狗、史莱姆等其他形态，主框架零改动。
- 可扩展的**动作/状态系统**：新增动作只需加文件 + 注册一行。
- 菜单栏图标（托盘）用于退出程序。
- 所有可调参数集中在 `config.py`。
- 直接 `python run.py` 脚本运行（第一版不打包）。

### 1.3 第一版明确不做（OUT-OF-SCOPE / YAGNI）
- 不支持点击/拖拽猫（纯观赏）。
- 不打包为 `.app`/`.exe`（脚本运行即可）。
- 不做运行时模型切换 UI（配置/参数指定模型）。
- 不做声音、不做与真实窗口的交互（爬窗框等）。
- 不引入第三方状态机库（自写轻量 FSM）。

## 2. 技术选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 语言 | Python 3.10 | 已安装；胶水层，开发迭代快 |
| GUI 框架 | **PySide6**（Qt6 官方 Python 绑定） | C++ 内核渲染性能足够；透明/无边框/置顶窗口原生支持；跨平台成熟；常驻内存 30-50MB，体积轻 |
| 鼠标追踪 | `QCursor.pos()` + QTimer 轮询 | 零权限、跨平台一致、足够第一版使用 |
| 状态机 | 自写轻量 FSM | 零依赖、完全可控、透明 |
| 素材 | 代码矢量绘制（QPainter） | 零依赖、零版权、可无限缩放、帧间一致性好 |

**排除方案**：Electron（常驻内存 100-200MB、体积 100MB+，不满足"轻量"）；Tauri（需 Rust，调试成本高）；Web 浏览器（无法监听全局鼠标，不算桌面宠物）。

## 3. 架构总览

### 3.1 三层分离（可扩展的根本保证）

| 层 | 职责 | 依赖方向 |
|----|------|---------|
| **State 层** | 决策"现在该做什么"——根据鼠标状态决定切换到哪个动作 | → Action 层 |
| **Action 层** | 执行具体动作——控制位置/朝向/姿态随时间变化，到点后通知完成 | ← 被 State 调用；→ Drawing 层 |
| **Drawing 层** | 纯绘制——给定姿态参数画猫，完全不知道状态/动作存在 | ← 被 Action 调用 |

### 3.2 模型抽象层（模型可替换的根本保证）

主框架（`app.py`/`window.py`/`pet_sprite.py`/`core/`）**完全不出现 "cat" 字样**，只依赖 `Model` 抽象基类。切换/新增模型时主框架零改动。

`Model` 基类契约：
- `name: str` —— 模型名，如 `"cat"`
- `draw(painter, pose, facing, t)` —— 根据姿态参数绘制；`pose` 是该模型自定义的**不透明**对象
- `create_state_machine(sprite) -> StateMachine` —— 返回该模型专属、已装配好的状态机
- `default_pose() -> Any` —— 模型初始姿态参数

**pose 不透明透传原则**：猫的 pose 和未来狗的 pose 结构不同，主框架只透传不解析，保证对不同形态的包容性。

### 3.3 模型切换
配置指定：`config.py` 中 `MODEL_NAME = "cat"`，或启动参数 `--model dog`。框架从 `models/` 目录加载对应模型。

## 4. 行为状态机（FSM）

### 4.1 状态列表（多状态，丰富体验）

| 状态 | 行为 | 主要转出条件 |
|------|------|-------------|
| **IDLE** | 在当前位置附近随机小幅游走；每隔 3-8 秒随机一个空闲小动作（坐/舔毛/伸懒腰） | 鼠标移动且速度<甩脱阈值 → CHASING；鼠标静止超 45s → SLEEPING |
| **CHASING** | 以中速向鼠标当前位置移动，朝向跟随 | 进入扑击距离且概率命中 → POUNCING；鼠标速度超甩脱阈值持续 0.3s → IDLE；鼠标静止 → IDLE |
| **POUNCING** | 先蓄力（压低身体 0.18s）→ 高速冲刺到鼠标当前位置 → 冲刺结束 | 冲刺完成 → IDLE |
| **SLEEPING** | 闭眼、冒鼻涕泡 | 鼠标有任何移动 → IDLE |
| **GROOMING** | 舔毛（独立状态，由 IDLE 的空闲动作轮选时触发进入） | 动作完成 → IDLE |

### 4.2 甩脱判定（用户选定：速度阈值方案）
- 连续追踪鼠标速度，计算**滑动平均**。
- 当滑动平均速度 > `ESCAPE_SPEED_PX_S`（默认 2500 px/s）**持续超过 `ESCAPE_DURATION_S`（默认 0.3s）**，判定甩脱，猫放弃追逐回到 IDLE。
- 用滑动平均而非瞬时速度，避免鼠标正常移动时偶尔的快速划动误触发。

### 4.3 扑击行为（用户选定：靠近后概率冲刺）
- 猫追到距离鼠标 < `POUNCE_TRIGGER_DIST_PX`（默认 80px）时，每帧以 `POUNCE_PROBABILITY`（默认 0.015，约每秒 0.9 次）的概率触发扑击。
- 扑击 = 蓄力（`POUNCE_WINDUP_S`=0.18s，身体压低）→ 高速冲刺（`POUNCE_SPEED_PX_S`=1200）到鼠标当前位置，冲刺距离上限 `POUNCE_MAX_DIST_PX`=250。

### 4.4 朝向（用户选定：只左右翻转）
猫根据移动方向（或朝向鼠标的方向）自动左右翻转。`facing ∈ {-1, +1}`。

## 5. 项目结构

```
desktop-cat/
├── README.md                  # 项目说明 + 运行方式
├── pyproject.toml             # 依赖声明、构建配置
├── requirements.txt           # pip 依赖（PySide6）
├── .gitignore
├── run.py                     # 入口：python run.py 一键启动；支持 --model
│
├── cat/                       # 主程序包
│   ├── __init__.py
│   ├── app.py                 # QApplication 启动、全局初始化、托盘图标
│   ├── window.py              # 透明置顶窗口 + 点击穿透 + 渲染画布（QGraphicsView）
│   ├── mouse_tracker.py       # 鼠标位置/速度采样（QTimer 轮询 + 滑动平均）
│   ├── config.py              # 所有可调参数集中在此
│   ├── tray.py                # 菜单栏托盘图标（退出）
│   │
│   ├── core/                  # 核心抽象（模型无关、动作无关）
│   │   ├── __init__.py
│   │   ├── state_machine.py   # 通用 FSM：State 基类 + 转换 + 事件分发
│   │   ├── action.py          # Action 基类（所有动作的抽象接口）
│   │   ├── pet_sprite.py      # 通用宠物实体：位置、朝向、当前动作、绘制委托给 Model
│   │   └── model.py           # Model 抽象基类 + 模型注册表/加载器
│   │
│   └── models/                # 模型库（一个目录一个模型）
│       ├── __init__.py        # 模型注册表：name -> Model 子类
│       └── cat/               # 猫模型（自包含）
│           ├── __init__.py
│           ├── model.py       # CatModel：实现 Model 接口，组装部件
│           ├── drawing.py     # 猫的 QPainter 矢量绘制（身体/头/耳/尾/眼/腿）
│           ├── poses.py       # 猫的各姿态几何参数 + Pose 数据类
│           ├── actions/       # 猫专属动作
│           │   ├── __init__.py
│           │   ├── walk.py
│           │   ├── run.py
│           │   ├── pounce.py
│           │   ├── sit.py
│           │   ├── sleep.py
│           │   ├── groom.py
│           │   └── stretch.py
│           └── states/        # 猫专属状态
│               ├── __init__.py
│               ├── idle_state.py
│               ├── chasing_state.py
│               ├── pouncing_state.py
│               ├── sleeping_state.py
│               └── grooming_state.py
│
├── tests/                     # 单元测试（纯逻辑，无 UI）
│   ├── test_state_machine.py
│   ├── test_mouse_tracker.py
│   └── test_actions.py
│
└── docs/
    └── superpowers/specs/
        └── 2026-07-16-desktop-cat-design.md   # 本文件
```

## 6. 核心抽象接口

### 6.1 Model 基类（`cat/core/model.py`）
```python
class Model(ABC):
    name: str
    @abstractmethod
    def draw(self, painter, pose, facing, t): ...
    @abstractmethod
    def create_state_machine(self, sprite) -> StateMachine: ...
    @abstractmethod
    def default_pose(self): ...
```

### 6.2 State 基类（`cat/core/state_machine.py`）
```python
class State:
    def on_enter(self, sprite): ...
    def on_exit(self, sprite): ...
    def update(self, sprite, dt, mouse_state): ...   # 每帧调用，可触发转换
    # 转换通过返回目标状态名或调用 fsm.transition_to(name) 实现
```

### 6.3 Action 基类（`cat/core/action.py`）
```python
class Action:
    def start(self, sprite): ...
    def update(self, sprite, dt): ...                  # 每帧调用
    def is_done(self) -> bool: ...
    on_done: Callable                                  # 完成回调
```

### 6.4 PetSprite（`cat/core/pet_sprite.py`）
通用宠物实体，模型无关。持有：位置 `(x, y)`、朝向 `facing`、当前姿态 `pose`、所属 `Model`、`StateMachine`。`update(dt, mouse_state)` 驱动 FSM；`draw(painter)` 委托给 `model.draw()`。

## 7. 配置参数（`cat/config.py`）

第一版用 Python 模块（未来可升级为 yaml）。所有数值为默认值，调手感时改本文件即可。

```python
MODEL_NAME = "cat"

# 鼠标追踪
MOUSE_POLL_HZ = 60              # 鼠标采样频率
ESCAPE_SPEED_PX_S = 2500        # 甩脱判定速度阈值
ESCAPE_DURATION_S = 0.3         # 超阈值持续多久判定甩脱
MOUSE_STILL_THRESHOLD_PX_S = 30 # 速度低于此视为"静止"

# 追逐行为
CHASE_SPEED_PX_S = 350          # 追逐速度
POUNCE_TRIGGER_DIST_PX = 80     # 进入此距离可能触发扑击
POUNCE_PROBABILITY = 0.015      # 每帧（在扑击距离内）触发扑击的概率
POUNCE_WINDUP_S = 0.18          # 扑击前蓄力时间
POUNCE_SPEED_PX_S = 1200        # 扑击冲刺速度
POUNCE_MAX_DIST_PX = 250        # 扑击最大冲刺距离

# 渲染
RENDER_FPS = 60
PET_SIZE_PX = 96                # 宠物的渲染尺寸（模型无关）

# 空闲行为
IDLE_WANDER_RADIUS_PX = 60      # IDLE 状态游走半径
IDLE_ACTION_INTERVAL_S = (3, 8) # 每隔 3-8 秒随机一个空闲动作
IDLE_SLEEP_AFTER_S = 45         # 鼠标静止超 45 秒进入 SLEEPING
```

## 8. 运行与退出

**运行**：
```bash
pip install -r requirements.txt
python run.py                  # 默认 cat 模型
python run.py --model dog      # 指定模型（未来）
```

**退出**（用户选定：菜单栏图标）：程序启动后在 macOS 菜单栏放一个 `QSystemTrayIcon`，点击菜单中的"退出"关闭程序。终端 `Ctrl+C` 作为备用退出。

## 9. 测试策略

- **纯逻辑层单元测试**（pytest）：FSM 状态转换、鼠标追踪的速度/滑动平均计算、动作的进度/完成判定、几何/缓动函数。
- **不测 UI**：窗口、绘制不写自动化测试（视觉验证为主）。
- 目标：核心逻辑有测试覆盖，调试时改参数有信心。

## 10. 关键风险与缓解

| 风险 | 缓解 |
|------|------|
| macOS 透明窗口点击穿透不彻底 | 用 `WA_TransparentForMouseEvents` + 窗口无焦点；若仍穿透不彻底，退化为整窗口不接收点击（纯观赏本就不需要点击） |
| 矢量猫画得丑 | 第一版接受卡通简笔风格；drawing.py 内颜色/形状参数集中，便于后续迭代画工 |
| 扑击手感不好 | 所有参数集中在 config.py，反复调参即可，不改逻辑 |
| 全局鼠标轮询在高分屏/多显示器坐标错乱 | 用 `QCursor.pos()` 返回的是虚拟桌面坐标，窗口覆盖整个虚拟桌面；多显示器边界 clamp 处理 |

## 11. 未来扩展（明确不在第一版，仅说明架构可支撑）

- 跨平台 Windows：PySide6 原生支持，透明窗口 API 一致，预计低改动。
- 新模型（狗/史莱姆）：新建 `models/<name>/` 实现 Model 接口即可，主框架零改动。
- 新动作（打哈欠/打滚）：新建 action 文件 + 注册一行 + 在某 State 触发。
- 运行时模型切换、声音、点击交互、打包为 .app：均为增量功能，不影响现有架构。
