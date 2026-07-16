"""核心抽象层（模型无关、动作无关）。

包含三个关键抽象：
- Model: 一个可插拔宠物的完整实现契约（绘制 + 状态机）
- State / StateMachine: 轻量有限状态机
- Action: 可复用的原子动作
- PetSprite: 通用宠物实体
"""
