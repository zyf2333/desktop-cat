"""模型库。导入本包会触发所有已注册子模型的登记。

新增模型（如 dog）：在 cat/models/<name>/ 创建 Model 子类，
并在本文件 import 一次即可进入注册表。
"""
from cat.models import cat        # noqa: F401  2D 矢量猫，触发注册
from cat.models import cat3d      # noqa: F401  3D 猫（Qt3D），触发注册
from cat.models import catsprite  # noqa: F401  精灵序列帧猫（贴图），触发注册
