"""外部 3D 模型加载器。

优先加载 assets/models/ 下的猫模型文件（.glb/.gltf/.obj），
找不到则回退到 low-poly 几何体拼装（builder.py）。

用法：把下载的猫模型放进 assets/models/，本模块自动检测加载。
支持的格式：.glb（推荐，单文件含贴图）、.gltf、.obj。
"""
from __future__ import annotations

import os
from typing import Optional

# 模型搜索目录（相对项目根）
_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "assets", "models",
)

# 支持的格式（按优先级）
_SUPPORTED_EXTS = (".glb", ".gltf", ".obj")


def find_cat_model() -> Optional[str]:
    """在 assets/models/ 查找猫模型文件，返回绝对路径；找不到返回 None。

    查找规则：优先 .glb，其次 .gltf，最后 .obj；
    文件名含 cat 的优先；否则取第一个匹配的。
    """
    if not os.path.isdir(_MODELS_DIR):
        return None
    # 收集所有支持的文件
    candidates = []
    for root, _dirs, files in os.walk(_MODELS_DIR):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in _SUPPORTED_EXTS:
                candidates.append(os.path.join(root, f))
    if not candidates:
        return None
    # 按优先级排序：名字含 cat 的优先，其次 .glb > .gltf > .obj
    def priority(p):
        name = os.path.basename(p).lower()
        ext = os.path.splitext(p)[1].lower()
        cat_bonus = 0 if "cat" in name else 100
        ext_order = {".glb": 0, ".gltf": 1, ".obj": 2}.get(ext, 3)
        return (cat_bonus, ext_order, p)
    candidates.sort(key=priority)
    return candidates[0]


def load_mesh(parent_entity, model_path: str):
    """用 QMesh 加载外部模型，返回 mesh 组件（已 setSource）。

    Args:
        parent_entity: 父 QEntity
        model_path: 模型文件绝对路径
    Returns:
        QMesh 组件（调用方负责 addComponent）
    """
    from PySide6.Qt3DRender import Qt3DRender
    from PySide6.QtCore import QUrl

    mesh = Qt3DRender.QMesh(parent_entity)
    mesh.setSource(QUrl.fromLocalFile(model_path))
    return mesh


def models_dir() -> str:
    """返回模型搜索目录路径（供提示用户放文件）。"""
    return _MODELS_DIR
