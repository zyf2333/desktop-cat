# 桌面宠物 · Desktop Pet

一只会追着鼠标跑、被甩脱就放弃、靠近时会突然扑过来的桌面宠物。
第一版是橘猫，架构支持替换为任意其他模型（狗、史莱姆……）。

![status](https://img.shields.io/badge/status-v0.1%20first%20version-orange)

## 特性

- 🐱 **追鼠标**：中速追踪鼠标移动
- 💨 **甩脱判定**：鼠标快速甩动（>2500px/s 持续 0.3s）后放弃追逐
- 🐾 **突然扑击**：靠近鼠标（<80px）时有概率蓄力后高速扑过去
- 😴 **丰富空闲**：溜达、坐、舔毛、伸懒腰、睡觉（鼠标久不动会睡着）
- 🎨 **纯矢量绘制**：QPainter 代码画猫，零图片素材、零版权、可缩放
- 🧩 **模型可替换**：主框架模型无关，新增模型 = 新建一个目录
- ⚡ **轻量**：常驻内存约 40-60MB

## 快速开始

### 依赖

- Python 3.10+
- macOS（第一版）；架构为跨平台设计，未来可支持 Windows

### 安装与运行

```bash
pip install -r requirements.txt
python run.py
```

启动后桌面会出现一只橘猫。**退出方式**：点击 macOS 菜单栏的宠物图标 → 退出。

### 指定模型（未来）

```bash
python run.py --model dog   # 当 cat/models/dog/ 实现后可用
```

## 调手感

所有可调参数集中在 [`cat/config.py`](cat/config.py)，改完直接重启即可，无需改逻辑代码。常用项：

| 参数 | 默认 | 含义 |
|------|------|------|
| `ESCAPE_SPEED_PX_S` | 2500 | 甩脱判定速度阈值 |
| `ESCAPE_DURATION_S` | 0.3 | 超阈值持续多久才判定甩脱 |
| `CHASE_SPEED_PX_S` | 350 | 追逐速度 |
| `POUNCE_TRIGGER_DIST_PX` | 80 | 进入此距离可能扑击 |
| `POUNCE_PROBABILITY` | 0.015 | 每帧扑击概率 |
| `POUNCE_SPEED_PX_S` | 1200 | 扑击冲刺速度 |
| `IDLE_SLEEP_AFTER_S` | 45 | 鼠标静止多久后睡觉 |
| `PET_SIZE_PX` | 96 | 宠物渲染尺寸 |
| `DEBUG` | False | True 时显示锚点/状态/速度等辅助信息 |

调试时设 `DEBUG=True` 可看到猫当前的状态和鼠标速度。

## 架构

三层分离 + 模型抽象，保证可扩展：

```
State 层（决策）   →  Action 层（执行）  →  Drawing 层（绘制）
                       ↑ Model 装配这三层
```

- **`cat/core/`**：模型无关的核心抽象（FSM、Action、PetSprite、Model 基类）
- **`cat/models/<name>/`**：一个自包含的宠物实现（绘制 + 动作 + 状态）
- 主框架（`app`/`window`/`mouse_tracker`）**完全不出现具体动物名**，只依赖 `Model` 抽象

详细设计见 [`docs/superpowers/specs/2026-07-16-desktop-cat-design.md`](docs/superpowers/specs/2026-07-16-desktop-cat-design.md)。

### 扩展指南

**新增一个动作**（如"打哈欠"）：
1. 新建 `cat/models/cat/actions/yawn.py`，继承 `cat.core.action.Action`
2. 在 `cat/models/cat/actions/__init__.py` 的 `ACTIONS` 字典注册一行
3. 在某个 State（如 IDLE）的空闲动作列表里加入它

**新增一个模型**（如狗）：
1. 新建 `cat/models/dog/`，实现 `DogModel`（继承 `cat.core.model.Model`）
2. 包含 `drawing.py`、`poses.py`、`actions/`、`states/`、`model.py`
3. 在 `cat/models/__init__.py` 加一行 `from cat.models import dog`
4. `python run.py --model dog` 即可，主框架零改动

## 测试

```bash
pytest
```

覆盖：几何/缓动工具、状态机转换、动作进度与完成、甩脱速度计算。

## 项目结构

```
desktop-cat/
├── run.py                     # 入口
├── cat/
│   ├── app.py                 # 应用组装（QApplication + 窗口 + 托盘）
│   ├── window.py              # 透明置顶点击穿透窗口
│   ├── mouse_tracker.py       # 鼠标采样 + 速度滑动平均 + 甩脱判定
│   ├── tray.py                # 菜单栏退出图标
│   ├── config.py              # 所有可调参数
│   ├── core/                  # 核心抽象（模型无关）
│   │   ├── state_machine.py   # 轻量 FSM
│   │   ├── action.py          # Action 基类
│   │   ├── pet_sprite.py      # 通用宠物实体
│   │   └── model.py           # Model 抽象基类 + 注册表
│   ├── models/cat/            # 猫模型（绘制 + 动作 + 状态）
│   └── utils/geometry.py      # 几何/缓动工具
└── tests/                     # 单元测试
```

## License

个人玩具项目，自由使用。
