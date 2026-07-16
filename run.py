#!/usr/bin/env python3
"""桌面宠物启动入口。

用法：
    python run.py                 # 用 config.py 中的默认模型
    python run.py --model dog     # 指定模型
"""
from cat.app import main

if __name__ == "__main__":
    raise SystemExit(main())
