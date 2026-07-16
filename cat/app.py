"""应用入口：组装 QApplication、窗口、托盘，运行事件循环。

被 run.py 调用。也可作为 python -m cat.app 入口。
"""
from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from cat import config
from cat.tray import TrayController
from cat.window import PetWindow


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="桌面宠物")
    parser.add_argument(
        "--model",
        default=config.MODEL_NAME,
        help=f"使用的模型（默认 {config.MODEL_NAME}）",
    )
    args = parser.parse_args(argv)

    app = QApplication(sys.argv[:1])  # 避免 Qt 吞掉 --model
    app.setQuitOnLastWindowClosed(False)  # 关键：托盘模式下不因隐藏窗口退出

    # 3D 模式必需：要求 surface format 带 alpha 通道，否则 Qt3D 透明背景
    # 会变成不透明黑底（alphaBufferSize 默认 -1）。
    from PySide6.QtGui import QSurfaceFormat
    fmt = QSurfaceFormat.defaultFormat()
    fmt.setAlphaBufferSize(8)
    QSurfaceFormat.setDefaultFormat(fmt)

    window = PetWindow(args.model)
    window.start()

    tray = TrayController(app)
    tray.show()

    code = app.exec()
    window.stop()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
