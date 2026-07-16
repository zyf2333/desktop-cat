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

from PySide6.QtCore import QElapsedTimer, QPointF, Qt, QTimer
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

        # 模型与精灵
        model = get_model(model_name)
        self._is_3d = bool(getattr(model, "is_3d", False))
        # 若 config 强制渲染模式，覆盖模型自报
        if config.RENDER_MODE == "2d":
            self._is_3d = False
        elif config.RENDER_MODE == "3d":
            self._is_3d = True
        self.sprite = PetSprite(
            model=model,
            x=self.width() / 2,
            y=self.height() / 2,
            size_px=config.PET_SIZE_PX,
        )
        self.sprite.start("idle")

        # 3D 渲染：构建 Qt3D 子窗口场景
        self._qt3d_view = None
        self._qt3d_container = None
        self._qt3d_root = None
        self._qt3d_root_transform = None
        if self._is_3d:
            self._setup_3d(model)

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

    def _setup_3d(self, model) -> None:
        """构建 Qt3D 透明渲染场景：相机、光照、猫的 entity 树。"""
        from PySide6.Qt3DCore import Qt3DCore
        from PySide6.Qt3DExtras import Qt3DExtras
        from PySide6.Qt3DRender import Qt3DRender
        from PySide6.QtGui import QColor, QVector3D

        self._qt3d_view = Qt3DExtras.Qt3DWindow()
        # 透明背景
        self._qt3d_view.defaultFrameGraph().setClearColor(QColor(0, 0, 0, 0))

        # 相机：正交投影（半高 = 猫的逻辑尺寸量级，让猫填满视野而非一个小点）
        # 配合侧视/俯视角露出身体长度和腿，避免正面看只剩一个大圆球。
        camera = self._qt3d_view.camera()
        half = config.CAMERA_ORTHO_HALF
        camera.lens().setOrthographicProjection(
            -half, half, -half, half, 0.1, 1000.0
        )
        # 相机略偏侧/俯：绕原点的球坐标
        import math as _m
        yaw = _m.radians(config.CAMERA_YAW)
        pitch = _m.radians(config.CAMERA_PITCH)
        dist = config.CAMERA_DISTANCE
        cx = dist * _m.cos(pitch) * _m.sin(yaw)
        cy = -dist * _m.sin(pitch)
        cz = dist * _m.cos(pitch) * _m.cos(yaw)
        camera.setPosition(QVector3D(cx, cy, cz))
        camera.setViewCenter(QVector3D(0, 0, 0))
        camera.setUpVector(QVector3D(0, 1, 0))

        # 根 entity（猫的整体位置/朝向挂这里）
        self._qt3d_root = Qt3DCore.QEntity()
        self._qt3d_root_transform = Qt3DCore.QTransform(self._qt3d_root)
        self._qt3d_root.addComponent(self._qt3d_root_transform)

        # 光照
        if config.ENABLE_3D_LIGHTING:
            light_entity = Qt3DCore.QEntity(self._qt3d_root)
            light = Qt3DRender.QDirectionalLight(light_entity)
            light.setWorldDirection(QVector3D(-0.5, -0.5, -1).normalized())
            light.setColor(QColor("#FFFFFF"))
            light.setIntensity(1.0)
            light_entity.addComponent(light)

        # 让模型构建猫的 entity 树
        model.build_3d_scene(self._qt3d_root)

        self._qt3d_view.setRootEntity(self._qt3d_root)

        # 嵌入 QWidget 容器（关键：保住外层 QWidget 的 setMask 穿透）
        self._qt3d_container = QWidget.createWindowContainer(self._qt3d_view, self)
        # 容器必须透明，否则会显示黑色底（配合 format alpha + view 透明清屏）
        self._qt3d_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._qt3d_container.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self._qt3d_container.setStyleSheet("background: transparent;")

    # ---- 生命周期 ----
    def start(self) -> None:
        # 不用 showFullScreen()：它在 macOS 会把窗口推入独立的"全屏 Space"。
        # 改用普通窗口 + 手动几何覆盖整个虚拟桌面 + 置顶。
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        geo = self.screen().virtualGeometry()
        self.setGeometry(geo)
        self.showNormal()
        self.raise_()
        # 强制置顶：macOS 上 WindowStaysOnTopHint 不足以压过所有窗口，
        # 用原生 API 把 NSWindow level 提到屏幕保护级。
        from cat.platform_topmost import force_topmost
        force_topmost(self)
        # 3D 模式：定位容器到宠物当前位置
        if self._is_3d and self._qt3d_container is not None:
            self._qt3d_container.show()
            self._position_3d_container()
        self._update_mask()
        interval_ms = int(1000 / config.RENDER_FPS)
        self._frame_timer.start(interval_ms)
        self._tracker.start()
        self._elapsed.restart()
        self._last_ms = 0

    def _position_3d_container(self) -> None:
        """把 Qt3D 容器定位到宠物当前位置（跟随宠物移动）。"""
        if self._qt3d_container is None:
            return
        size = config.PET_SIZE_PX * 2
        x = int(self.sprite.x - size / 2)
        y = int(self.sprite.y - size / 2)
        self._qt3d_container.setGeometry(x, y, size, size)

    def stop(self) -> None:
        self._frame_timer.stop()
        self._tracker.stop()

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
        self.setMask(region)

    # ---- 点击 ----
    def mousePressEvent(self, event) -> None:
        pos = event.position()
        x, y = pos.x(), pos.y()
        if self.sprite.contains(x, y):
            self.sprite.on_click(x, y)
            self.update()
        # 不调 super，让掩码外区域天然穿透

    # ---- 鼠标追踪 ----
    def _on_mouse(self, state: MouseState) -> None:
        self._latest_mouse = state

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

        if self._is_3d:
            # 3D 模式：每帧推进自驱动 + 渲染 + 跟随定位容器
            t = time.monotonic() - self._global_t0
            self.sprite.model.advance(self.sprite.pose, t)
            self.sprite.model.render_3d(
                self._qt3d_root, self.sprite.pose, self.sprite.facing, t,
                config.CAT3D_SCALE,
            )
            self._position_3d_container()
        else:
            # 2D 模式：触发重绘
            self.update()

    # ---- 绘制（仅 2D 模式）----
    def paintEvent(self, _event) -> None:
        if self._is_3d:
            return  # 3D 由 Qt3D 容器自渲染
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
