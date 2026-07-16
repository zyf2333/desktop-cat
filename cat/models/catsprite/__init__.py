"""精灵序列帧猫模型（贴图渲染）。导入即注册。"""
from cat.core.model import register
from cat.models.catsprite.model import CatSpriteModel

register(CatSpriteModel())

__all__ = ["CatSpriteModel"]
