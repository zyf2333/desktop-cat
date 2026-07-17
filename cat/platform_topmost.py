"""跨平台强制置顶工具。

Qt 的 WindowStaysOnTopHint 在 macOS 上不足以压过所有应用窗口
（其他置顶窗口、某些全屏应用仍会盖住）。本模块用平台原生 API
把窗口层级提升到屏幕保护级，确保真正永远置顶。

macOS：通过 ctypes 调 AppKit，拿 NSWindow 设 level=1000+（NSScreenSaverLevel）。
其他平台：回退到 Qt 标志（够用）。
"""
from __future__ import annotations

import sys


def force_topmost(widget, aggressive: bool = False) -> None:
    """把 widget 提升到系统最高窗口层级。

    macOS 用 NSWindow.setLevel 设到屏幕保护级（压过普通应用窗口）。
    aggressive=True 时额外调 orderFrontRegardless 强制到最前（不管焦点），
    但会打断用户当前操作，仅在启动/必要时用。

    Args:
        widget: 要置顶的 QWidget
        aggressive: 是否强制抢到最前（会打断用户焦点，慎用）
    """
    if sys.platform != "darwin":
        widget.raise_()
        return

    try:
        _mac_set_level(widget, level=1001)  # 略高于 NSScreenSaverWindowLevel(1000)
        if aggressive:
            _mac_order_front(widget)  # 强制到前面（不管焦点）
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


def _mac_order_front(widget) -> None:
    """macOS: 强制窗口显示到最前面（不管当前焦点在哪个应用）。

    用 orderFrontRegardless（不抢键盘焦点，只是视觉上到最前）。
    解决"点击其他窗口后猫被遮挡"的问题。
    """
    import ctypes
    import ctypes.util

    objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
    view_ptr = int(widget.winId())

    objc.sel_registerName.restype = ctypes.c_void_p
    objc.sel_registerName.argtypes = [ctypes.c_char_p]
    objc.objc_msgSend.restype = ctypes.c_void_p
    objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    def sel(name: str):
        return objc.sel_registerName(name.encode())

    nsview = ctypes.c_void_p(view_ptr)
    nswindow = objc.objc_msgSend(nsview, sel("window"))
    if not nswindow:
        return

    # [NSWindow orderFrontRegardless] —— 强制到前面，不管焦点
    objc.objc_msgSend.restype = None
    objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    objc.objc_msgSend(ctypes.c_void_p(nswindow), sel("orderFrontRegardless"))
