"""猫模型包。导入即注册到全局注册表。"""
from cat.core.model import register
from cat.models.cat.model import CatModel

# 单例注册（保持轻量；状态机在 create_state_machine 中每次按需创建）
register(CatModel())

__all__ = ["CatModel"]
