"""应用入口：组装 QApplication、窗口、托盘，运行事件循环。

被 run.py 调用。也可作为 python -m cat.app 入口。
"""
from __future__ import annotations

import argparse
import sys

from cat import config
from cat.qt import QApplication, exec_app
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

    window = PetWindow(args.model)
    window.start()

    tray = TrayController(app)
    tray.show()

    code = exec_app(app)
    window.stop()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
