"""Model（模型）抽象 —— 模型可替换的根本保证。

一个 Model 是一个自包含的宠物实现包：提供绘制函数、专属状态机、初始姿态。
主框架只依赖 Model 抽象，不出现任何具体动物名。

切换模型：在 config.py 设置 MODEL_NAME，框架通过 load_model() 加载对应实现。
新增模型：在 cat/models/<name>/ 实现 Model 子类，并在 registry 登记。

pose 透传原则：pose 是模型自定义的不透明对象（猫和狗的结构不同），
框架只透传不解析，保证对不同形态的包容性。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from cat.qt import QPainter

    from .pet_sprite import PetSprite
    from .state_machine import StateMachine


class Model(ABC):
    """一个可插拔宠物模型的实现契约。"""

    #: 模型名，如 "cat"。子类必须覆盖。
    name: str = "base"

    @abstractmethod
    def advance(self, pose: Any, t: float) -> None:
        """推进渲染无关的自驱动状态（呼吸/眨眼/摆尾相位等）。每帧由窗口层调用。"""

    @abstractmethod
    def draw(self, painter: "QPainter", pose: Any, facing: int, t: float, size_px: int) -> None:
        """根据姿态用 QPainter 绘制。"""

    @abstractmethod
    def create_state_machine(self, sprite: "PetSprite") -> "StateMachine":
        """返回该模型专属、已装配好全部状态的状态机。"""

    @abstractmethod
    def default_pose(self) -> Any:
        """返回该模型的初始姿态对象。"""


# ---- 注册表与加载 ----
# name -> Model 实例。模型包在自己的 __init__ 里调用 register 进行登记。
_REGISTRY: Dict[str, Model] = {}


def register(model: Model) -> None:
    """登记一个模型实例。"""
    if model.name in _REGISTRY and _REGISTRY[model.name] is not model:
        raise ValueError(f"模型 '{model.name}' 已注册")
    _REGISTRY[model.name] = model


def available_models() -> Dict[str, Model]:
    """返回所有已注册模型。"""
    return dict(_REGISTRY)


def get_model(name: str) -> Model:
    """按名字获取模型；不存在则抛 KeyError。"""
    # 触发模型包导入，确保注册表被填充（cat.models 的 __init__ 会导入 cat 子模型）
    import cat.models  # noqa: F401  保证子模型被导入并注册
    if name not in _REGISTRY:
        raise KeyError(
            f"未知模型 '{name}'。可选：{sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[name]
