"""资源路径解析（兼容开发模式和打包模式）。

打包后（PyInstaller），程序运行时资源被解压到 sys._MEIPASS 临时目录，
相对路径 __file__ 会变。本模块统一处理：

- 开发模式：资源在项目根的 assets/ 目录
- 打包模式（frozen）：资源在 sys._MEIPASS/assets/ 目录
"""
from __future__ import annotations

import os
import sys


def resource_root() -> str:
    """返回资源根目录。

    - 打包模式（PyInstaller frozen）：返回 sys._MEIPASS（临时解压目录）
    - 开发模式：返回项目根目录
    """
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后，资源在 _MEIPASS
        return sys._MEIPASS  # type: ignore[attr-defined]
    # 开发模式：项目根 = 本文件(cat/paths.py) 的上两级
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset_path(*parts: str) -> str:
    """获取 assets/ 下的资源绝对路径。

    用法：asset_path("sprites", "idle_01.png") → /path/to/assets/sprites/idle_01.png
    """
    return os.path.join(resource_root(), "assets", *parts)
