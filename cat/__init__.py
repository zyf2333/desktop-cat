"""桌面宠物主程序包。

设计原则：
- 主框架（app/window/mouse_tracker/config/tray）完全模型无关，不出现具体动物名。
- 具体宠物实现位于 cat/models/<name>/，通过 core.model.Model 抽象接入。
"""
