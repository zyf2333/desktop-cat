"""PetSprite —— 通用宠物实体（模型无关）。

持有宠物的运行时状态：位置、朝向、姿态、当前动作；并把绘制委托给 Model。
窗口层每帧调用 sprite.update() 推进 FSM，再调用 sprite.draw() 绘制。

设计要点：
- PetSprite 不知道自己是什么动物，所有"猫/狗"细节都在 Model 里。
- pose 是 Model 提供的不透明对象，Action 直接读写它的字段。
- facing 由 Action/State 根据移动方向设置；绘制时 Model 负责按 facing 翻转。
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Optional

from .action import Action
from .model import Model
from .personality import Personality
from .state_machine import StateMachine

if TYPE_CHECKING:
    from PySide6.QtGui import QPainter


class PetSprite:
    """一只宠物的运行时数据与驱动。"""

    def __init__(
        self,
        model: Model,
        x: float,
        y: float,
        size_px: int,
        personality: Optional["Personality"] = None,
    ) -> None:
        self.model: Model = model
        self.x: float = x
        self.y: float = y
        self.size_px: int = size_px
        self.facing: int = 1  # +1 朝右，-1 朝左
        self.pose: Any = model.default_pose()

        # 个性（per-instance）。未提供时从 config 取默认值。
        if personality is None:
            from cat import config  # 延迟 import 避免循环
            personality = Personality(**config.PERSONALITY)
        self.personality: Personality = personality.clamp()

        # 状态机由模型装配
        self.fsm: StateMachine = model.create_state_machine(self)

        # 当前动作（可能为 None：表示"无动作"，由状态自己直接驱动 pose）
        self._action: Optional[Action] = None

        # 最新鼠标状态（每帧由 update 刷新），供 Action/State 读取
        self.mouse_state = None

        # 玩弄冷却：玩腻退出 playing 时设的时间戳，在此之前不再进 playing。
        # 避免"玩腻→idle→鼠标还在脚下→立刻又 playing"的死循环。
        self.play_cooldown_until: float = 0.0

        # 窗口交互状态。拖拽期间暂停 Action/FSM，避免猫一边被拖一边自己跑。
        self.is_hovered: bool = False
        self.is_dragging: bool = False
        self.world_bounds = (0.0, 0.0, 4000.0, 3000.0)

        # 跨状态累计的清醒时间。舔毛、疯跑等动作不会把困意清零。
        from cat import config
        self.awake_seconds: float = 0.0
        self.sleep_after_seconds: float = random.uniform(*config.AUTONOMOUS_SLEEP_AFTER_S)
        self.droppings = []

    # ---- 生命周期 ----
    def start(self, initial_state: str) -> None:
        """启动状态机，进入初始状态。"""
        self.fsm.start(initial_state)

    def update(self, dt: float, mouse_state) -> None:
        """每帧驱动：先推进当前 Action，再驱动 FSM。"""
        self.mouse_state = mouse_state
        if self.is_dragging:
            return
        if self.fsm.current_name != "sleeping":
            self.awake_seconds += dt
        action = self._action
        if action is not None:
            action.update(self, dt)
            # 仅当仍是同一个 action 且它已完成时才清理。
            # 注意：action.update 可能触发 finish→on_done→transition_to→
            #       新状态 on_enter 中的 play/clear_action，此时 _action 已被替换，
            #       不应再动它。
            if self._action is action and action.is_done():
                self._action = None
        self.fsm.update(dt, mouse_state)
        # 推进特效粒子（独立于 action，shed 结束后已生成的粒子继续飘落）
        self._update_particles(dt)

    def _update_particles(self, dt: float) -> None:
        """推进挂在 sprite 上的特效粒子（掉毛等）。"""
        import math
        particles = getattr(self, "fur_particles", None)
        if not particles:
            return
        gravity = 30.0
        alive = []
        for p in particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += gravity * dt
            p.vx *= 0.98
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.rot += p.rot_v * dt
            alive.append(p)
        self.fur_particles = alive

    def draw(self, painter: "QPainter", t: float) -> None:
        """绘制：平移到宠物中心，委托给 model.draw；再画特效粒子（掉毛等）。"""
        painter.save()
        painter.translate(self.x, self.y)
        # 先推进渲染无关的自驱动状态（呼吸/眨眼），再委托绘制
        self.model.advance(self.pose, t)
        # facing 翻转交给 model.draw 内部处理（保持中心对称）
        self.model.draw(painter, self.pose, self.facing, t, self.size_px)
        painter.restore()
        # 特效粒子（相对猫中心坐标，由 Action 产生挂在 sprite 上）
        self._draw_particles(painter)
        self._draw_droppings(painter)

    def _draw_particles(self, painter: "QPainter") -> None:
        """绘制挂在 sprite 上的特效粒子（如掉毛毛絮）。"""
        particles = getattr(self, "fur_particles", None)
        if not particles:
            return
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtGui import QColor
        painter.save()
        painter.translate(self.x, self.y)
        painter.setPen(Qt.PenStyle.NoPen)
        for p in particles:
            # 透明度随生命衰减
            alpha = max(0, min(180, int(180 * (p.life / p.max_life))))
            painter.setBrush(QColor(245, 240, 230, alpha))
            painter.save()
            painter.translate(p.x, p.y)
            painter.rotate(p.rot)
            painter.drawEllipse(QPointF(0, 0), p.size, p.size * 0.5)
            painter.restore()
        painter.restore()

    def _draw_droppings(self, painter: "QPainter") -> None:
        if not self.droppings:
            return
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtGui import QColor, QPainter, QPen
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        for dropping in self.droppings:
            outline = QColor(55, 30, 18)
            brown = QColor(112, 67, 38)
            painter.setPen(QPen(outline, 2))
            painter.setBrush(brown)
            s = dropping.size
            painter.drawEllipse(QPointF(dropping.x, dropping.y), s, s * 0.52)
            painter.drawEllipse(QPointF(dropping.x, dropping.y - s * 0.55), s * 0.7, s * 0.48)
            painter.drawEllipse(QPointF(dropping.x, dropping.y - s), s * 0.4, s * 0.36)
        painter.restore()

    def dropping_at(self, x: float, y: float):
        """返回命中的便便；从后往前找，优先处理最后绘制的一个。"""
        for dropping in reversed(self.droppings):
            rx = dropping.size * 1.35
            ry = dropping.size * 1.8
            if rx <= 0 or ry <= 0:
                continue
            dx = (x - dropping.x) / rx
            dy = (y - (dropping.y - dropping.size * 0.45)) / ry
            if dx * dx + dy * dy <= 1.0:
                return dropping
        return None

    def remove_dropping_at(self, x: float, y: float) -> bool:
        """只有显式点击命中时才移除便便。"""
        dropping = self.dropping_at(x, y)
        if dropping is None:
            return False
        self.droppings.remove(dropping)
        return True

    # ---- 动作控制（供 State 调用）----
    def play(self, action: Action, on_done: Optional[Any] = None) -> None:
        """开始播放一个动作。完成时触发 on_done（若提供）。"""
        action.on_done = on_done
        self._action = action
        action.start(self)

    @property
    def has_action(self) -> bool:
        return self._action is not None

    @property
    def current_action(self) -> Optional[Action]:
        return self._action

    def clear_action(self) -> None:
        """强制中止当前动作（不触发 on_done）。供状态切换时清理用。"""
        self._action = None

    # ---- 点击交互（局部热区）----
    @property
    def hit_radius(self) -> float:
        """点击命中半径（屏幕像素）。约 size_px 的 0.85 倍。"""
        return self.size_px * 0.85

    def contains(self, x: float, y: float) -> bool:
        """某点是否在宠物的圆形热区内。"""
        import math
        return math.hypot(x - self.x, y - self.y) <= self.hit_radius

    def on_click(self, x: float, y: float) -> None:
        """被点击时的反应钩子。

        第一版：被点 → 跳起 + 短暂困惑（像被吓到）。
        未来可扩展：喂食、抚摸等不同区域的反应。
        """
        # 朝向点击来源
        if x < self.x:
            self.facing = -1
        else:
            self.facing = 1
        # 中止当前动作，切到困惑（被吓一跳）
        self.clear_action()
        if self.fsm is not None:
            # 睡觉时被点 → 醒来困惑
            self.fsm.transition_to("confused")

    def on_hover(self, x: float, y: float) -> None:
        """鼠标第一次移到宠物身上时，立刻抬头警觉。"""
        if self.is_hovered or self.is_dragging:
            return
        self.is_hovered = True
        self.facing = -1 if x < self.x else 1
        # 让反应在下一帧绘制前就可见，同时进入完整捕猎前摇。
        if hasattr(self.pose, "ear_alert"):
            self.pose.ear_alert = 1.0
        if hasattr(self.pose, "pupil_dilate"):
            self.pose.pupil_dilate = 0.8
        self.clear_action()
        self.fsm.transition_to("alert")

    def on_hover_leave(self) -> None:
        self.is_hovered = False

    def begin_drag(self) -> None:
        """开始拖动；动作暂停，位置交给窗口层更新。"""
        self.is_dragging = True
        self.is_hovered = True
        self.clear_action()
        if hasattr(self.pose, "body_lift"):
            self.pose.body_lift = 10.0
        if hasattr(self.pose, "leg_stride"):
            self.pose.leg_stride = 0.0

    def drag_to(self, x: float, y: float) -> None:
        if not self.is_dragging:
            return
        left, top, right, bottom = self.world_bounds
        margin = self.size_px * 0.35
        self.x = max(left + margin, min(right - margin, x))
        self.y = max(top + margin, min(bottom - margin, y))

    def end_drag(self) -> None:
        """放下后短暂困惑，再恢复自主行为。"""
        if not self.is_dragging:
            return
        self.is_dragging = False
        if hasattr(self.pose, "body_lift"):
            self.pose.body_lift = 0.0
        self.fsm.transition_to("confused")
