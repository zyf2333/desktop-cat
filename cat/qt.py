"""Qt 绑定兼容层。

默认使用 PySide6；Windows 7 专用构建通过环境变量显式选择 PySide2。
业务模块只从这里导入 Qt 类型，避免绑定版本判断散落在各处。
"""
from __future__ import annotations

import os


_QT_API = os.environ.get("DESKTOP_CAT_QT_API", "").strip().lower()
if _QT_API not in ("", "pyside6", "pyside2"):
    raise RuntimeError(f"不支持的 DESKTOP_CAT_QT_API: {_QT_API}")

_use_pyside2 = _QT_API == "pyside2"
if not _use_pyside2:
    try:
        from PySide6.QtCore import (
            QElapsedTimer,
            QObject,
            QPoint,
            QPointF,
            QRectF,
            Qt,
            QTimer,
            Signal,
        )
        from PySide6.QtGui import (
            QAction,
            QColor,
            QCursor,
            QGuiApplication,
            QIcon,
            QPainter,
            QPainterPath,
            QPen,
            QPixmap,
            QPolygonF,
            QRegion,
        )
        from PySide6.QtWidgets import (
            QApplication,
            QMenu,
            QSizePolicy,
            QSystemTrayIcon,
            QWidget,
        )

        QT_BINDING = "PySide6"
    except ImportError:
        if _QT_API == "pyside6":
            raise
        _use_pyside2 = True

if _use_pyside2:
    from PySide2.QtCore import (  # type: ignore[no-redef]
        QElapsedTimer,
        QObject,
        QPoint,
        QPointF,
        QRectF,
        Qt,
        QTimer,
        Signal,
    )
    from PySide2.QtGui import (  # type: ignore[no-redef]
        QColor,
        QCursor,
        QGuiApplication,
        QIcon,
        QPainter,
        QPainterPath,
        QPen,
        QPixmap,
        QPolygonF,
        QRegion,
    )
    from PySide2.QtWidgets import (  # type: ignore[no-redef]
        QAction,
        QApplication,
        QMenu,
        QSizePolicy,
        QSystemTrayIcon,
        QWidget,
    )

    QT_BINDING = "PySide2"


def exec_app(app: QApplication) -> int:
    """运行兼容 Qt5/Qt6 的应用事件循环。"""
    runner = getattr(app, "exec", None)
    if runner is None:
        runner = app.exec_
    return runner()


__all__ = [
    "QAction",
    "QApplication",
    "QColor",
    "QCursor",
    "QElapsedTimer",
    "QGuiApplication",
    "QIcon",
    "QMenu",
    "QObject",
    "QPainter",
    "QPainterPath",
    "QPen",
    "QPixmap",
    "QPoint",
    "QPointF",
    "QPolygonF",
    "QRectF",
    "QRegion",
    "QSizePolicy",
    "QSystemTrayIcon",
    "QTimer",
    "QT_BINDING",
    "Qt",
    "QWidget",
    "Signal",
    "exec_app",
]
