"""透明、无边框、始终置顶、局部点击响应的桌面覆盖窗口。

负责：
- 建立覆盖整个虚拟桌面的透明窗口
- 维护 PetSprite 并以固定帧率驱动 + 重绘
- 把鼠标状态分发到 sprite

点击交互（局部热区）：
- 用 setMask 每帧跟随宠物设置一个圆形可点击区域
- 圆外区域完全穿透（不影响其他应用操作）
- 圆内点击 → 触发 sprite.on_click 反应
"""
from __future__ import annotations

import time

from PySide6.QtCore import QElapsedTimer, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from cat import config
from cat.core.model import get_model
from cat.core.pet_sprite import PetSprite
from cat.mouse_tracker import MouseState, MouseTracker


class PetWindow(QWidget):
    """全屏透明覆盖窗口，承载并绘制宠物。"""

    def __init__(self, model_name: str) -> None:
        # FramelessWindowHint + Tool（不在任务栏出现）+ StayOnTop
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        # 透明背景（但保留鼠标事件接收能力，由 setMask 控制热区）
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setFixedSize(self.screen().virtualSize().width(),
                          self.screen().virtualSize().height())
        self.move(0, 0)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

        # 模型与精灵
        model = get_model(model_name)
        self.sprite = PetSprite(
            model=model,
            x=self.width() / 2,
            y=self.height() / 2,
            size_px=config.PET_SIZE_PX,
        )
        self.sprite.world_bounds = (0.0, 0.0, float(self.width()), float(self.height()))
        self.sprite.start("idle")

        self._press_pos = None
        self._drag_offset = (0.0, 0.0)
        self._dragging = False

        # 鼠标追踪
        self._tracker = MouseTracker()
        self._latest_mouse: MouseState = MouseState(
            pos=(self.sprite.x, self.sprite.y),
            speed_smooth=0.0,
            is_escaping=False,
            still_seconds=0.0,
            moving=False,
        )
        self._tracker.state_changed.connect(self._on_mouse)

        # 帧驱动：用 QTimer + elapsed 计算真实 dt
        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        self._last_ms = 0
        self._frame_timer = QTimer(self)
        self._frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._frame_timer.timeout.connect(self._tick)
        self._global_t0 = time.monotonic()

    # ---- 生命周期 ----
    def start(self) -> None:
        # 不用 showFullScreen()：它在 macOS 会把窗口推入独立的"全屏 Space"。
        # 改用普通窗口 + 手动几何覆盖整个虚拟桌面 + 置顶。
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        geo = self.screen().virtualGeometry()
        self.setGeometry(geo)
        self.showNormal()
        self.raise_()
        self._update_mask()
        interval_ms = int(1000 / config.RENDER_FPS)
        self._frame_timer.start(interval_ms)
        self._tracker.start()
        self._elapsed.restart()
        self._last_ms = 0
        # 强制置顶：macOS 上 WindowStaysOnTopHint 不足以压过所有窗口。
        # 用原生 API 把 NSWindow level 提到屏幕保护级（压过普通应用）。
        # 启动时 aggressive 一次（强制到最前），之后周期性只重设 level
        # （不抢焦点，避免打断用户打字/看视频）。
        from cat.platform_topmost import force_topmost
        from PySide6.QtCore import QTimer
        force_topmost(self, aggressive=True)  # 启动：强制到最前
        QTimer.singleShot(300, lambda: force_topmost(self, aggressive=True))  # 显示后重保
        self._topmost_timer = QTimer(self)
        self._topmost_timer.timeout.connect(lambda: force_topmost(self))  # 只重设 level
        self._topmost_timer.start(2000)  # 每 2 秒重设一次 level

    def stop(self) -> None:
        self._frame_timer.stop()
        self._tracker.stop()
        if hasattr(self, "_topmost_timer"):
            self._topmost_timer.stop()

    # ---- 局部热区 ----
    def _update_mask(self) -> None:
        """根据宠物当前位置更新可点击的圆形区域。

        setMask 让掩码外区域对鼠标完全透明（穿透到底层应用），
        掩码内可接收点击。每帧调用以跟随宠物移动。
        离屏平台（offscreen）不支持 mask，跳过。
        """
        from PySide6.QtGui import QGuiApplication, QRegion
        try:
            if QGuiApplication.platformName() == "offscreen":
                return
        except Exception:
            pass
        r = int(self.sprite.hit_radius)
        cx, cy = int(self.sprite.x), int(self.sprite.y)
        region = QRegion(cx - r, cy - r, 2 * r, 2 * r, QRegion.RegionType.Ellipse)
        # 便便是持久桌面元素，需要纳入窗口可见区域；范围很小，尽量不影响点击。
        for dropping in self.sprite.droppings:
            s = max(4, int(dropping.size * 1.4))
            region = region.united(QRegion(
                int(dropping.x) - s,
                int(dropping.y) - s * 2,
                s * 2,
                s * 3,
                QRegion.RegionType.Ellipse,
            ))
        self.setMask(region)

    # ---- 点击 ----
    def mousePressEvent(self, event) -> None:
        pos = event.position()
        x, y = pos.x(), pos.y()
        if event.button() == Qt.MouseButton.LeftButton and self.sprite.remove_dropping_at(x, y):
            self._update_mask()
            self.update()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self.sprite.contains(x, y):
            # 先记下按压；移动超过阈值才算拖拽，否则释放时按普通点击处理。
            self._press_pos = QPointF(x, y)
            self._drag_offset = (self.sprite.x - x, self.sprite.y - y)
            event.accept()
            return
        event.ignore()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        x, y = pos.x(), pos.y()
        if self._press_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            moved = ((x - self._press_pos.x()) ** 2 + (y - self._press_pos.y()) ** 2) ** 0.5
            if moved >= 4.0 and not self._dragging:
                self._dragging = True
                self.sprite.begin_drag()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            if self._dragging:
                self.sprite.drag_to(x + self._drag_offset[0], y + self._drag_offset[1])
                self._update_mask()
                self.update()
            event.accept()
            return
        if self.sprite.contains(x, y):
            self.sprite.on_hover(x, y)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif self.sprite.dropping_at(x, y) is not None:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.unsetCursor()
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._press_pos is None:
            event.ignore()
            return
        pos = event.position()
        if self._dragging:
            self.sprite.end_drag()
        else:
            self.sprite.on_click(pos.x(), pos.y())
        self._press_pos = None
        self._dragging = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._update_mask()
        self.update()
        event.accept()

    def enterEvent(self, event) -> None:
        pos = event.position()
        # mask 还包含便便的小区域；只有真正进入猫的热区才触发警觉。
        if self.sprite.contains(pos.x(), pos.y()):
            self.sprite.on_hover(pos.x(), pos.y())
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if not self._dragging:
            self.sprite.on_hover_leave()
            self.unsetCursor()
        super().leaveEvent(event)

    # ---- 鼠标追踪 ----
    def _on_mouse(self, state: MouseState) -> None:
        self._latest_mouse = state
        # 透明窗口的 mask 会随猫移动，enter/leave 事件偶尔可能缺失；
        # 用真实全局鼠标位置每次校准，避免悬停标记残留导致刚睡就醒。
        local = self.mapFromGlobal(QPoint(int(state.pos[0]), int(state.pos[1])))
        inside = self.sprite.contains(local.x(), local.y())
        if inside and not self.sprite.is_hovered and not self.sprite.is_dragging:
            self.sprite.on_hover(local.x(), local.y())
        elif not inside and self.sprite.is_hovered and not self.sprite.is_dragging:
            self.sprite.on_hover_leave()

    # ---- 主循环 ----
    def _tick(self) -> None:
        now_ms = self._elapsed.elapsed()
        dt = (now_ms - self._last_ms) / 1000.0
        self._last_ms = now_ms
        if dt <= 0 or dt > 0.1:
            dt = 1.0 / config.RENDER_FPS

        self.sprite.update(dt, self._latest_mouse)
        # 跟随宠物更新热区
        self._update_mask()
        # 触发重绘
        self.update()

    # ---- 绘制 ----
    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # 整窗透明（不清背景色）
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        t = time.monotonic() - self._global_t0
        self.sprite.draw(painter, t)

        if config.DEBUG:
            self._draw_debug(painter)

    def _draw_debug(self, painter: QPainter) -> None:
        painter.setPen(Qt.GlobalColor.red)
        # 猫锚点
        painter.drawEllipse(
            int(self.sprite.x) - 3, int(self.sprite.y) - 3, 6, 6
        )
        # 热区圆
        r = int(self.sprite.hit_radius)
        painter.setPen(Qt.GlobalColor.cyan)
        painter.drawEllipse(QPointF(self.sprite.x, self.sprite.y), r, r)
        # 状态名
        painter.setPen(Qt.GlobalColor.yellow)
        painter.drawText(
            int(self.sprite.x) + 10,
            int(self.sprite.y) - 10,
            f"{self.sprite.fsm.current_name} speed={self._latest_mouse.speed_smooth:.0f}",
        )
