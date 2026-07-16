"""3D 猫模型包（low-poly，Qt3D 渲染）。导入即注册到全局注册表。"""
from cat.core.model import register
from cat.models.cat3d.model import Cat3DModel

register(Cat3DModel())

__all__ = ["Cat3DModel"]
