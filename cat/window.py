"""透明、无边框、始终置顶、点击穿透的桌面覆盖窗口。

负责：
- 建立覆盖整个虚拟桌面的透明窗口
- 维护 PetSprite 并以固定帧率驱动 + 重绘
- 把鼠标状态分发到 sprite

点击穿透：第一版纯观赏，整个窗口设为对鼠标事件透明
（WA_TransparentForMouseEvents），鼠标点击直接穿过到底层应用。
"""
from __future__ import annotations

import time

from PySide6.QtCore import QElapsedTimer, Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from cat import config
from cat.core.model import get_model
from cat.core.pet_sprite import PetSprite
from cat.mouse_tracker import MouseState, MouseTracker


class PetWindow(QWidget):
    """全屏透明覆盖窗口，承载并绘制宠物。"""

    def __init__(self, model_name: str) -> None:
        # FramelessWindowHint + Tool（不在任务栏出现）+ StayOnTop + 无透明背景
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        # 完全透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setFixedSize(self.screen().virtualSize().width(),
                          self.screen().virtualSize().height())
        self.move(0, 0)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # 模型与精灵
        model = get_model(model_name)
        self.sprite = PetSprite(
            model=model,
            x=self.width() / 2,
            y=self.height() / 2,
            size_px=config.PET_SIZE_PX,
        )
        self.sprite.start("idle")

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
        # 不用 showFullScreen()：它在 macOS 会把窗口推入独立的"全屏 Space"，
        # 那是一个全新的黑色桌面，而不是覆盖在用户当前桌面上。
        # 改用普通窗口 + 手动几何覆盖整个虚拟桌面 + 置顶，达到"贴在桌面上"的效果。
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # 重新覆盖整个虚拟桌面（多显示器情况）
        geo = self.screen().virtualGeometry()
        self.setGeometry(geo)
        self.showNormal()
        self.raise_()
        interval_ms = int(1000 / config.RENDER_FPS)
        self._frame_timer.start(interval_ms)
        self._tracker.start()
        self._elapsed.restart()
        self._last_ms = 0

    def stop(self) -> None:
        self._frame_timer.stop()
        self._tracker.stop()

    # ---- 鼠标 ----
    def _on_mouse(self, state: MouseState) -> None:
        self._latest_mouse = state

    # ---- 主循环 ----
    def _tick(self) -> None:
        now_ms = self._elapsed.elapsed()
        dt = (now_ms - self._last_ms) / 1000.0
        self._last_ms = now_ms
        # 防止切屏回来后的巨大 dt
        if dt <= 0 or dt > 0.1:
            dt = 1.0 / config.RENDER_FPS

        self.sprite.update(dt, self._latest_mouse)
        # 仅重绘宠物所在区域附近（简化：整窗 update，足够流畅）
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
        # 状态名
        painter.setPen(Qt.GlobalColor.yellow)
        painter.drawText(
            int(self.sprite.x) + 10,
            int(self.sprite.y) - 10,
            f"{self.sprite.fsm.current_name} speed={self._latest_mouse.speed_smooth:.0f}",
        )
