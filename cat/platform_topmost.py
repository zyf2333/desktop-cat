"""跨平台强制置顶工具。

Qt 的 WindowStaysOnTopHint 在 macOS 上不足以压过所有应用窗口
（其他置顶窗口、某些全屏应用仍会盖住）。本模块用平台原生 API
把窗口层级提升到屏幕保护级，确保真正永远置顶。

macOS：通过 ctypes 调 AppKit，拿 NSWindow 设 level=1000+（NSScreenSaverLevel）。
其他平台：回退到 Qt 标志（够用）。
"""
from __future__ import annotations

import sys


def force_topmost(widget) -> None:
    """把 widget 提升到系统最高窗口层级。

    macOS 用 NSWindow.setLevel；其他平台仅 raise_()。
    需在 widget.show() 之后调用。
    """
    if sys.platform != "darwin":
        widget.raise_()
        return

    try:
        _mac_set_level(widget, level=1001)  # 略高于 NSScreenSaverWindowLevel(1000)
    except Exception:
        # 任何原生调用失败都回退到 Qt
        widget.raise_()


def _mac_set_level(widget, level: int) -> None:
    """macOS: 通过 ctypes 拿 NSView→NSWindow，设 level。"""
    import ctypes
    import ctypes.util

    # 加载 AppKit / Foundation 框架
    appkit = ctypes.cdll.LoadLibrary(ctypes.util.find_library("AppKit"))
    objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))

    # 拿 QWidget 的 NSView（PySide6 widget 的 winId 返回 NSView 指针）
    view_ptr = int(widget.winId())

    # objc_msgSend 声明
    objc.objc_msgSend.restype = ctypes.c_void_p
    objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    def sel(name: str):
        return objc.sel_registerName(name.encode())  # type: ignore[attr-defined]

    objc.sel_registerName.restype = ctypes.c_void_p
    objc.sel_registerName.argtypes = [ctypes.c_char_p]

    # [NSView window] 取 NSWindow
    nsview = ctypes.c_void_p(view_ptr)
    nswindow = objc.objc_msgSend(nsview, sel("window"))
    if not nswindow:
        widget.raise_()
        return

    # [NSWindow setLevel:level]
    objc.objc_msgSend.restype = None
    objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
    objc.objc_msgSend(ctypes.c_void_p(nswindow), sel("setLevel:"), ctypes.c_int(level))
