"""个性系统（模型无关）。

一只宠物的行为个性。每个维度是 [0, 1] 的浮点数，影响动作参数的调节。

设计要点：
- Personality 挂在 PetSprite 上（per-instance），支持多宠物不同个性。
- 动作通过 sprite.personality.<dim> 读取，调节自身速度/时长/概率等。
- 默认值从 config.PERSONALITY 读，启动时注入。
- 新增个性维度 = 这里加字段 + 在用到的地方读取，主框架零改动。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Personality:
    """宠物个性。所有维度 [0,1]，0=低，1=高。"""

    liveliness: float = 0.7    # 活泼度：追逐速度、动作频率、尾巴摆幅
    alertness: float = 0.5     # 警觉度：警觉范围、反应速度
    patience: float = 0.6      # 耐心：潜行持续时间、放弃速度（高=有耐心）
    playfulness: float = 0.6   # 玩心：进入 PLAYING 概率、玩弄时长
    curiosity: float = 0.5     # 好奇心：嗅闻/探索倾向

    def clamp(self) -> "Personality":
        """返回所有维度被限制在 [0,1] 的副本。"""
        return Personality(
            liveliness=max(0.0, min(1.0, self.liveliness)),
            alertness=max(0.0, min(1.0, self.alertness)),
            patience=max(0.0, min(1.0, self.patience)),
            playfulness=max(0.0, min(1.0, self.playfulness)),
            curiosity=max(0.0, min(1.0, self.curiosity)),
        )
