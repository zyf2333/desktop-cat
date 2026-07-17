#!/usr/bin/env python3
"""打包后瘦身：删除 .app/.exe 目录里无用的大模块。

PyInstaller 的 excludes 管不到 Qt 的 framework 二进制（它们被 hook 自动收集），
所以打包后需要手动删除用不到的 Qt 模块，把体积从 ~600MB 降到 ~80MB。

用法：
    python scripts/strip_app.py        # macOS：清 dist/DesktopCat.app
    python scripts/strip_app.py win    # Windows：清 dist/DesktopCat
"""
from __future__ import annotations

import os
import shutil
import sys


# 要删除的 Qt 模块（framework 名 / .so 名 / dll 名前缀）
# 我们只用 QtCore / QtGui / QtWidgets，其他全删
_QT_TRASH_PATTERNS = [
    # 3D
    'Qt3D', 'QtQuick3D',
    # WebEngine / WebChannel / WebSockets
    'QtWebEngine', 'QtWebChannel', 'QtWebSockets',
    # Quick / QML
    'QtQuick', 'QtQml', 'QtQmlModels', 'QtQmlWorkerScript', 'QtLabsQml',
    'QtLabsFolderListModel', 'QtLabsSettings', 'QtLabsAnimation',
    # 多媒体
    'QtMultimedia', 'QtSpatialAudio', 'QtTextToSpeech',
    # 图表/数据可视化/PDF
    'QtCharts', 'QtDataVisualization', 'QtDataVisualizationQml',
    'QtPdf', 'QtQuickShapes', 'QtQuickTemplates2', 'QtQuickParticles',
    'QtQuickDialogs2', 'QtQuickEffects', 'QtQuickLayouts',
    # 网络/位置/传感器/蓝牙/NFC
    'QtNetwork', 'QtNetworkAuth', 'QtPositioning', 'QtLocation',
    'QtSensors', 'QtSerialBus', 'QtSerialPort', 'QtBluetooth', 'QtNfc',
    'QtRemoteObjects',
    # SQL/测试/帮助/设计器
    'QtSql', 'QtTest', 'QtHelp', 'QtDesigner', 'QtUiTools',
    'QtPrintSupport', 'QtScxml', 'QtStateMachine', 'QtVirtualKeyboard',
    'QtShaderTools', 'QtQuick3DAssetUtils', 'QtQuick3DUtils',
    'QtQuick3DRuntimeRender', 'QtQuick3DAssets',
    # ffmpeg/多媒体编解码（QtMultimedia 的依赖）
    'libav', 'swscale', 'swresample', 'avcodec', 'avformat', 'avutil',
]

# PySide6 的 .so / .py 模块（同名前缀删除）
_PYSIDE6_TRASH_PREFIXES = [
    'Qt3D', 'QtWebEngine', 'QtWebChannel', 'QtWebSockets',
    'QtQuick', 'QtQml', 'QtMultimedia', 'QtSpatialAudio',
    'QtCharts', 'QtDataVisualization', 'QtPdf', 'QtNetwork',
    'QtNetworkAuth', 'QtPositioning', 'QtLocation', 'QtSensors',
    'QtSerialBus', 'QtSerialPort', 'QtBluetooth', 'QtNfc',
    'QtRemoteObjects', 'QtSql', 'QtTest', 'QtHelp', 'QtDesigner',
    'QtUiTools', 'QtPrintSupport', 'QtScxml', 'QtStateMachine',
    'QtVirtualKeyboard', 'QtShaderTools', 'QtTextToSpeech',
]


def _matches_trash(name: str) -> bool:
    """文件/目录名是否匹配要删除的模式。"""
    for p in _QT_TRASH_PATTERNS:
        if p in name:
            return True
    return False


def strip_macos(app_path: str) -> None:
    """清理 macOS .app。"""
    contents = os.path.join(app_path, 'Contents')
    total_freed = 0

    # 1. 删 Resources/PySide6（与 Frameworks/PySide6 重复，55MB）
    res_pyside = os.path.join(contents, 'Resources', 'PySide6')
    if os.path.isdir(res_pyside):
        size = _path_size(res_pyside)
        shutil.rmtree(res_pyside)
        total_freed += size
        print(f"  删除 Resources/PySide6 ({_human(size)})")

    # 2. 清理 Frameworks/PySide6
    fw_pyside = os.path.join(contents, 'Frameworks', 'PySide6')
    if os.path.isdir(fw_pyside):
        # 2a. 删 PySide6 的 .so/.py 模块
        for entry in os.listdir(fw_pyside):
            full = os.path.join(fw_pyside, entry)
            if any(entry.startswith(pre) for pre in _PYSIDE6_TRASH_PREFIXES):
                size = _path_size(full)
                shutil.rmtree(full) if os.path.isdir(full) else os.remove(full)
                total_freed += size
                print(f"  删除 {entry} ({_human(size)})")
            # 2b. 删 Qt 开发工具（qmlls/qmlformat/Assistant/Linguist/Designer 等）
            elif entry in ('qmlls', 'qmlformat', 'qmake', 'qmlcachegen',
                           'qmlimportscanner', 'qmltyperegistrar',
                           'Assistant.app', 'Linguist.app', 'Designer.app',
                           'pixeltool.app', 'qhelpgenerator'):
                size = _path_size(full)
                shutil.rmtree(full) if os.path.isdir(full) else os.remove(full)
                total_freed += size
                print(f"  删除 {entry} ({_human(size)})")
        # 2c. 删 Qt framework（只留 Core/Gui/Widgets/OpenGL/Svg/Concurrent/DBus）
        keep_qt = {'QtCore.framework', 'QtGui.framework', 'QtWidgets.framework',
                   'QtOpenGL.framework', 'QtSvg.framework', 'QtDBus.framework',
                   'QtConcurrent.framework'}
        qt_lib = os.path.join(fw_pyside, 'Qt', 'lib')
        if os.path.isdir(qt_lib):
            for entry in os.listdir(qt_lib):
                if entry not in keep_qt:
                    p = os.path.join(qt_lib, entry)
                    size = _path_size(p)
                    shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
                    total_freed += size
                    print(f"  删除 Qt/lib/{entry} ({_human(size)})")
        # 2d. 删无用 plugins（只保留基本显示相关）
        qt_plugins = os.path.join(fw_pyside, 'Qt', 'plugins')
        if os.path.isdir(qt_plugins):
            for entry in os.listdir(qt_plugins):
                if entry not in ('platforms', 'styles', 'imageformats',
                                 'accessible', 'iconengines', 'platformthemes'):
                    p = os.path.join(qt_plugins, entry)
                    size = _path_size(p)
                    shutil.rmtree(p)
                    total_freed += size
                    print(f"  删除 plugins/{entry} ({_human(size)})")

    print(f"\n共释放 {_human(total_freed)}")


def strip_windows(app_dir: str) -> None:
    """清理 Windows 目录。"""
    pyside_dir = os.path.join(app_dir, 'PySide6')
    total_freed = 0
    if os.path.isdir(pyside_dir):
        for entry in os.listdir(pyside_dir):
            name = entry.lower()
            if any(pre.lower() in name for pre in _PYSIDE6_TRASH_PREFIXES + _QT_TRASH_PATTERNS):
                p = os.path.join(pyside_dir, entry)
                size = _path_size(p)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
                total_freed += size
                print(f"  删除 {entry} ({_human(size)})")
    print(f"\n共释放 {_human(total_freed)}")


def _path_size(path: str) -> int:
    if os.path.isfile(path):
        return os.path.getsize(path)
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def _human(n: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def main():
    platform = sys.argv[1] if len(sys.argv) > 1 else ('darwin' if sys.platform == 'darwin' else 'win')
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist = os.path.join(base, 'dist')

    if platform in ('darwin', 'mac', 'macos'):
        app = os.path.join(dist, 'DesktopCat.app')
        if not os.path.isdir(app):
            print(f"找不到 {app}，先打包：pyinstaller desktop-cat.spec")
            return 1
        print(f"清理 macOS .app: {app}")
        strip_macos(app)
        final = _human(_path_size(app))
        print(f"最终 .app 体积: {final}")
    else:
        app = os.path.join(dist, 'DesktopCat')
        if not os.path.isdir(app):
            print(f"找不到 {app}，先打包：pyinstaller desktop-cat.spec")
            return 1
        print(f"清理 Windows 目录: {app}")
        strip_windows(app)
        final = _human(_path_size(app))
        print(f"最终目录体积: {final}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
