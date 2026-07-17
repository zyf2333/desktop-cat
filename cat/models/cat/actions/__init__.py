"""猫的动作库 —— 族+变体两级命名空间。

每个"族"（family）代表一类动作（如 sit、pounce、play），族下有多个"变体"（variant）
代表同类的不同表现（如 sit.relax 放松坐、sit.alert 警觉坐）。

扩展口契约（加新变体）：
1. 实现 Action 子类
2. 在 REGISTRY[family] 加一行 "variant": XxxAction
3. 主框架/状态机零改动

扩展口契约（加新族）：
1. 实现 Action 子类
2. 在 REGISTRY 加 "family": {"variant": XxxAction}
3. 在对应 State 里 make_action("family") 调用
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, Optional, Type

from cat.core.action import Action
from cat.models.cat.actions._helpers import reset_to_stand
from cat.models.cat.actions.alert import AlertAction
from cat.models.cat.actions.chase import ChaseAction
from cat.models.cat.actions.confused import ConfusedAction
from cat.models.cat.actions.groom import GroomAction
from cat.models.cat.actions.jump_pounce import JumpPounceAction
from cat.models.cat.actions.notice import NoticeAction
from cat.models.cat.actions.pounce import PounceAction
from cat.models.cat.actions.run import RunAction
from cat.models.cat.actions.shed import ShedAction
from cat.models.cat.actions.sit import SitAction
from cat.models.cat.actions.sleep import SleepAction
from cat.models.cat.actions.sniff import SniffAction
from cat.models.cat.actions.stalk import StalkAction
from cat.models.cat.actions.stretch import StretchAction
from cat.models.cat.actions.swat import SwatAction
from cat.models.cat.actions.walk import WalkAction
from cat.models.cat.actions.wrestle import WrestleAction

if TYPE_CHECKING:
    from cat.core.pet_sprite import PetSprite

# 族 → {变体名 → 动作类}
REGISTRY: Dict[str, Dict[str, Type[Action]]] = {
    # 捕猎链
    "alert":    {"default": AlertAction},
    "notice":   {"default": NoticeAction},
    "stalk":    {"default": StalkAction},
    "pounce":   {"default": PounceAction},
    "chase":    {"default": ChaseAction},
    "run":      {"default": RunAction},
    # 困惑
    "confused": {"default": ConfusedAction},
    # 玩弄（逗猫棒玩法）：4 个变体，按个性加权选择
    "play": {
        "swat": SwatAction,            # 爪拍
        "jump_pounce": JumpPounceAction,  # 跳扑
        "wrestle": WrestleAction,      # 扭打玩
        "sniff": SniffAction,          # 嗅闻
    },
    # 空闲
    "walk":     {"default": WalkAction},
    "sit":      {"default": SitAction},
    "sleep":    {"default": SleepAction},
    "groom":    {"default": GroomAction},
    "stretch":  {"default": StretchAction},
    "shed":     {"default": ShedAction},   # 掉毛
}

# 空闲动作选择表（带权重）。variant=None 表示由 make_action 按个性随机选变体。
# 扩展：加新空闲动作 = 这里加一条 + REGISTRY 注册。
IDLE_ACTIONS = [
    {"family": "sit", "variant": None, "weight": 3},
    {"family": "stretch", "variant": None, "weight": 1},
    {"family": "groom", "variant": None, "weight": 2},
    {"family": "shed", "variant": None, "weight": 2},   # 掉毛
]

# 各族的默认变体（族只有 default 变体时用）
_DEFAULT_VARIANT = "default"


def make_action(
    family: str,
    variant: Optional[str] = None,
    sprite: "Optional[PetSprite]" = None,
    **kwargs,
) -> Action:
    """统一动作工厂。State 永远通过它创建动作。

    Args:
        family: 动作族名，如 "sit"、"pounce"
        variant: 变体名；None 时按个性/随机选一个变体
        sprite: 宠物实体（用于个性驱动的变体选择；可选）
        **kwargs: 传给动作构造函数的参数（如 target=...）
    """
    if family not in REGISTRY:
        raise KeyError(f"未知动作族 '{family}'，可选：{sorted(REGISTRY.keys())}")
    family_map = REGISTRY[family]
    if variant is None:
        variant = _pick_variant(family, family_map, sprite)
    if variant not in family_map:
        raise KeyError(f"族 '{family}' 无变体 '{variant}'，可选：{sorted(family_map.keys())}")
    return family_map[variant](**kwargs)


def _pick_variant(family: str, family_map: Dict[str, Type[Action]], sprite) -> str:
    """按个性选择变体。族只有 default 时直接返回 default。

    多变体族按个性加权：play 族根据 playfulness/curiosity/liveliness 选不同玩法。
    扩展新族的多变体逻辑：在此加 elif 分支。
    """
    if len(family_map) == 1 and _DEFAULT_VARIANT in family_map:
        return _DEFAULT_VARIANT

    if family == "play" and sprite is not None:
        p = sprite.personality
        # 各玩法的基础权重 + 个性调节
        weights = {
            "swat":       3.0 + p.playfulness * 2.0,                # 玩心高爱拍
            "jump_pounce": 1.0 + p.liveliness * 3.0,                 # 活泼爱跳扑
            "wrestle":    1.0 + p.playfulness * 2.0 + p.liveliness,  # 玩心+活泼爱扭打
            "sniff":      2.0 + p.curiosity * 4.0,                   # 好奇爱嗅
        }
        variants = [v for v in weights if v in family_map]
        w = [weights[v] for v in variants]
        return random.choices(variants, weights=w, k=1)[0]

    # 其他多变体族：等权随机
    return random.choice(list(family_map.keys()))


def weighted_choice(table, sprite: "Optional[PetSprite]" = None) -> dict:
    """按权重从选择表随机选一项。

    Args:
        table: IDLE_ACTIONS 形式的列表，每项含 weight
        sprite: 预留个性加权（未来活泼的猫可能提升 walk 权重）
    """
    weights = [item["weight"] for item in table]
    return random.choices(table, weights=weights, k=1)[0]


__all__ = [
    "REGISTRY",
    "IDLE_ACTIONS",
    "make_action",
    "weighted_choice",
    "reset_to_stand",
]
