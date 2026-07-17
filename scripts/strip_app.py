#!/usr/bin/env python3
"""打包后瘦身：删除 .app/.exe 目录里无用的大模块。

PyInstaller 的 excludes 管不到 Qt 的 framework/dll 二进制（它们被 hook 自动收集），
所以打包后需要手动删除用不到的 Qt 模块，把体积从 ~600MB 降到 ~80MB。

所有删除操作都容错（_safe_remove），删不了的跳过不报错，
确保瘦身（只是体积优化）不会阻断打包流程。

用法：
    python scripts/strip_app.py        # macOS：清 dist/DesktopCat.app
    python scripts/strip_app.py win    # Windows：清 dist/DesktopCat
"""
from __future__ import annotations

import os
import shutil
import sys


# 我们只用 QtCore/QtGui/QtWidgets，其他 Qt 模块全删
# 按文件/目录名包含的子串匹配（大小写不敏感）
_QT_TRASH_PATTERNS = [
    'Qt3D', 'QtQuick3D',
    'QtWebEngine', 'QtWebChannel', 'QtWebSockets',
    'QtQuick', 'QtQml', 'QtLabsQml', 'QtLabsFolderListModel',
    'QtLabsSettings', 'QtLabsAnimation',
    'QtMultimedia', 'QtSpatialAudio', 'QtTextToSpeech',
    'QtCharts', 'QtDataVisualization', 'QtPdf',
    'QtNetwork', 'QtNetworkAuth', 'QtPositioning', 'QtLocation',
    'QtSensors', 'QtSerialBus', 'QtSerialPort', 'QtBluetooth', 'QtNfc',
    'QtRemoteObjects', 'QtSql', 'QtTest', 'QtHelp', 'QtDesigner',
    'QtUiTools', 'QtPrintSupport', 'QtScxml', 'QtStateMachine',
    'QtVirtualKeyboard', 'QtShaderTools',
    'QtHttpServer', 'QtGraphs', 'QtLottie', 'QtCanvasPainter',
    # ffmpeg/编解码
    'libav', 'avcodec', 'avformat', 'avutil', 'swscale', 'swresample',
]

# Qt 开发工具（可执行文件/app），删除
_QT_DEV_TOOLS = {
    'qmlls', 'qmlformat', 'qmake', 'qmlcachegen', 'qmlimportscanner',
    'qmltyperegistrar', 'qhelpgenerator',
    'Assistant.app', 'Linguist.app', 'Designer.app', 'pixeltool.app',
}

# macOS 要保留的 Qt framework
_MAC_KEEP_FRAMEWORKS = {
    'QtCore.framework', 'QtGui.framework', 'QtWidgets.framework',
    'QtOpenGL.framework', 'QtSvg.framework', 'QtDBus.framework',
    'QtConcurrent.framework',
}

# 要保留的 plugins 子目录
_KEEP_PLUGINS = {
    'platforms', 'styles', 'imageformats',
    'accessible', 'iconengines', 'platformthemes',
}


def _path_size(path: str) -> int:
    """文件/目录大小（容错）。"""
    if os.path.isfile(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0
    total = 0
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    return total


def _human(n: float) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def _safe_remove(path: str) -> int:
    """安全删除，返回释放字节。失败返回 0 不报错（容错，不阻断流程）。"""
    if not os.path.exists(path):
        return 0
    size = _path_size(path)
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        if size > 0:
            print(f"  删除 {os.path.basename(path)} ({_human(size)})")
        return size
    except (OSError, PermissionError) as e:
        print(f"  跳过（无法删除）: {os.path.basename(path)}")
        return 0


def _matches_trash(name: str) -> bool:
    """名字是否匹配要删除的 Qt 模块（大小写不敏感）。"""
    lower = name.lower()
    return any(p.lower() in lower for p in _QT_TRASH_PATTERNS)


def strip_macos(app_path: str) -> int:
    """清理 macOS .app。返回释放字节数。"""
    contents = os.path.join(app_path, 'Contents')
    total = 0

    # 1. 删 Resources/PySide6（与 Frameworks 重复）
    total += _safe_remove(os.path.join(contents, 'Resources', 'PySide6'))

    fw_pyside = os.path.join(contents, 'Frameworks', 'PySide6')
    if os.path.isdir(fw_pyside):
        # 2. 删 PySide6 的无用模块 .so + 开发工具
        for entry in os.listdir(fw_pyside):
            full = os.path.join(fw_pyside, entry)
            if _matches_trash(entry) or entry in _QT_DEV_TOOLS:
                total += _safe_remove(full)
        # 3. 删 Qt framework（只留核心几个）
        qt_lib = os.path.join(fw_pyside, 'Qt', 'lib')
        if os.path.isdir(qt_lib):
            for entry in os.listdir(qt_lib):
                if entry not in _MAC_KEEP_FRAMEWORKS:
                    total += _safe_remove(os.path.join(qt_lib, entry))
        # 4. 删无用 plugins
        qt_plugins = os.path.join(fw_pyside, 'Qt', 'plugins')
        if os.path.isdir(qt_plugins):
            for entry in os.listdir(qt_plugins):
                if entry not in _KEEP_PLUGINS:
                    total += _safe_remove(os.path.join(qt_plugins, entry))

    print(f"\n共释放 {_human(total)}")
    return total


def strip_windows(app_dir: str) -> int:
    """清理 Windows 目录。返回释放字节数。"""
    total = 0
    # PySide6 可能在 _internal/PySide6 或直接 PySide6
    for pyside_dir in (os.path.join(app_dir, 'PySide6'),
                       os.path.join(app_dir, '_internal', 'PySide6')):
        if not os.path.isdir(pyside_dir):
            continue
        for entry in os.listdir(pyside_dir):
            full = os.path.join(pyside_dir, entry)
            # 删无用模块（.pyd / .py / .dll）+ 开发工具
            if _matches_trash(entry) or entry in _QT_DEV_TOOLS:
                total += _safe_remove(full)
        # 删 Qt 的 dll（PySide6/Qt6/bin 或 PySide6 根目录下的 .dll）
        qt_bin = os.path.join(pyside_dir, 'Qt6', 'bin')
        if os.path.isdir(qt_bin):
            for entry in os.listdir(qt_bin):
                if _matches_trash(entry):
                    total += _safe_remove(os.path.join(qt_bin, entry))
        # 删无用 plugins
        qt_plugins = os.path.join(pyside_dir, 'plugins')
        if os.path.isdir(qt_plugins):
            for entry in os.listdir(qt_plugins):
                if entry not in _KEEP_PLUGINS:
                    total += _safe_remove(os.path.join(qt_plugins, entry))
        # 删 translations（用不到）
        total += _safe_remove(os.path.join(pyside_dir, 'translations'))
        # 删 examples / qml（如有）
        total += _safe_remove(os.path.join(pyside_dir, 'examples'))
        total += _safe_remove(os.path.join(pyside_dir, 'qml'))

    print(f"\n共释放 {_human(total)}")
    return total


def main():
    platform_arg = sys.argv[1] if len(sys.argv) > 1 else ('darwin' if sys.platform == 'darwin' else 'win')
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist = os.path.join(base, 'dist')

    if platform_arg in ('darwin', 'mac', 'macos'):
        app = os.path.join(dist, 'DesktopCat.app')
        if not os.path.isdir(app):
            print(f"找不到 {app}，先打包：pyinstaller desktop-cat.spec")
            return 1
        print(f"清理 macOS .app: {app}")
        strip_macos(app)
        print(f"最终 .app 体积: {_human(_path_size(app))}")
    else:
        app = os.path.join(dist, 'DesktopCat')
        if not os.path.isdir(app):
            print(f"找不到 {app}，先打包：pyinstaller desktop-cat.spec")
            return 1
        print(f"清理 Windows 目录: {app}")
        strip_windows(app)
        print(f"最终目录体积: {_human(_path_size(app))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
