#!/usr/bin/env python3
"""桌面宠物启动入口，包含打包版崩溃日志。

用法：
    python run.py                 # 用 config.py 中的默认模型
    python run.py --model dog     # 指定模型
"""
import datetime
import faulthandler
import os
import platform
import sys
import traceback


_log_file = None


def _log_path() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "DesktopCat")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "crash.log")


def _show_error(log_path: str) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            None,
            f"DesktopCat 启动或运行出错。\n错误日志：\n{log_path}",
            "DesktopCat 错误",
            0x10,
        )
    except Exception:
        pass


def _install_crash_log() -> str:
    global _log_file
    path = _log_path()
    _log_file = open(path, "a", encoding="utf-8")
    _log_file.write(
        f"\n[{datetime.datetime.now().isoformat()}] "
        f"Python={platform.python_version()} OS={platform.platform()}\n"
    )
    _log_file.flush()
    faulthandler.enable(_log_file, all_threads=True)

    def handle(exc_type, exc_value, exc_tb):
        traceback.print_exception(exc_type, exc_value, exc_tb, file=_log_file)
        _log_file.flush()
        _show_error(path)

    sys.excepthook = handle
    return path

if __name__ == "__main__":
    log_path = _install_crash_log()
    try:
        from cat.app import main
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException:
        sys.excepthook(*sys.exc_info())
        raise SystemExit(1)
