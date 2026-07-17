"""精灵序列帧加载器。

从 assets/sprites/ 加载 PNG 序列帧，按动画名分组缓存。
命名约定：<anim>_<NN>.png（如 cat_walk_00.png），同前缀的归为同一动画。

动画 → 状态机动作映射（在 model.py 里定义）。
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from PySide6.QtGui import QPixmap

from cat.paths import asset_path

# sprites 目录（兼容打包模式：打包后用 sys._MEIPASS，开发模式用项目根）
_SPRITES_DIR = asset_path("sprites")

# 全局帧缓存：anim_name -> [QPixmap, ...]
_cache: Dict[str, List[QPixmap]] = {}


def sprites_dir() -> str:
    return _SPRITES_DIR


def load_all() -> Dict[str, List[QPixmap]]:
    """加载 sprites 目录下所有序列帧，返回 {anim: [frames]}。

    扫描所有 <prefix>_<NN>.png，按 prefix 分组并按 NN 排序。
    """
    if _cache:
        return _cache
    if not os.path.isdir(_SPRITES_DIR):
        return _cache
    groups: Dict[str, List[Tuple[int, str]]] = {}
    for fname in os.listdir(_SPRITES_DIR):
        if not fname.lower().endswith(".png"):
            continue
        # 解析 prefix 和序号：cat_walk_00.png -> prefix=cat_walk, idx=0
        stem = os.path.splitext(fname)[0]
        # 从末尾找最后一个 _ 后的数字
        parts = stem.rsplit("_", 1)
        if len(parts) != 2 or not parts[1].isdigit():
            continue
        prefix = parts[0]
        idx = int(parts[1])
        groups.setdefault(prefix, []).append((idx, os.path.join(_SPRITES_DIR, fname)))
    for prefix, items in groups.items():
        items.sort(key=lambda x: x[0])
        _cache[prefix] = [QPixmap(p) for _, p in items]
    return _cache


def get_animation(name: str) -> List[QPixmap]:
    """取某个动画的所有帧；未加载则触发加载。"""
    if not _cache:
        load_all()
    return _cache.get(name, [])


def available_animations() -> List[str]:
    """返回所有可用动画名。"""
    if not _cache:
        load_all()
    return sorted(_cache.keys())
