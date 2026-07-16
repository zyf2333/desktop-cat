"""菜单栏托盘图标：用于退出程序（因为透明窗口没有关闭按钮）。

macOS 上会出现在屏幕顶部菜单栏。提供"退出"菜单项。
"""
from __future__ import annotations

from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def _make_icon() -> QIcon:
    """生成一个简单的程序图标（橙色圆点带猫耳剪影），无外部素材。"""
    from PySide6.QtCore import Qt, QPointF
    from PySide6.QtGui import QColor, QPainter, QPolygonF

    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    # 圆脸
    p.setBrush(QColor("#E8820E"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(6, 8, 20, 20)
    # 两只耳朵（三角）
    ear_l = QPolygonF([QPointF(8, 9), QPointF(11, 2), QPointF(14, 9)])
    ear_r = QPolygonF([QPointF(18, 9), QPointF(21, 2), QPointF(24, 9)])
    p.drawPolygon(ear_l)
    p.drawPolygon(ear_r)
    p.end()
    return QIcon(pix)


class TrayController:
    """托盘图标控制器。"""

    def __init__(self, app: QApplication) -> None:
        self.app = app
        self._tray = QSystemTrayIcon(_make_icon(), app)
        self._tray.setToolTip("桌面宠物 · 点击退出")
        menu = QMenu()
        act_quit = QAction("退出", menu)
        act_quit.triggered.connect(self._on_quit)
        menu.addAction(act_quit)
        self._tray.setContextMenu(menu)
        # 单击托盘也弹出菜单
        self._tray.activated.connect(self._on_activated)

    def show(self) -> None:
        self._tray.show()

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._tray.contextMenu().popup(
                self._tray.geometry().center()
            )

    def _on_quit(self) -> None:
        self._tray.hide()
        self.app.quit()
