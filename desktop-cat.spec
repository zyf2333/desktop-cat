# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置（macOS / Windows 通用）。

打包产出 dist/DesktopCat.app（macOS）或 dist/DesktopCat/DesktopCat.exe（Windows）。
用户双击即可启动，无需安装 Python 或依赖。

用法：
    pyinstaller desktop-cat.spec --noconfirm

macOS 产出：dist/DesktopCat.app（双击启动）
Windows 产出：dist/DesktopCat/DesktopCat.exe（双击启动）
"""
import sys
import os
import shutil
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# 把 assets/ 目录（精灵素材）作为数据文件打进包
datas = [
    ('assets', 'assets'),
]

# 排除的 PySide6/Qt 模块（我们只用 QtCore/QtGui/QtWidgets，其他全删）
# 这些是体积大头：QtWebEngineCore 单独就 216MB
_EXCLUDE_MODULES = [
    # 3D 相关（已移除的功能）
    'PySide6.Qt3DCore', 'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras',
    'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender',
    # WebEngine（浏览器引擎，216MB，我们不用）
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineQuick', 'PySide6.QtWebChannel',
    'PySide6.QtWebSockets',
    # Quick/QML（ declarative UI，不用）
    'PySide6.QtQuick', 'PySide6.QtQuick3D', 'PySide6.QtQuickControls2',
    'PySide6.QtQuickWidgets', 'PySide6.QtQuickTest', 'PySide6.QtQml',
    # 多媒体/图表/数据可视化（不用）
    'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
    'PySide6.QtCharts', 'PySide6.QtDataVisualization',
    'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
    'PySide6.QtSpatialAudio', 'PySide6.QtTextToSpeech',
    'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtPositioning',
    'PySide6.QtLocation', 'PySide6.QtSensors', 'PySide6.QtSerialPort',
    'PySide6.QtSerialBus', 'PySide6.QtRemoteObjects',
    'PySide6.QtScxml', 'PySide6.QtStateMachine',
    'PySide6.QtSql', 'PySide6.QtTest', 'PySide6.QtHelp',
    'PySide6.QtDesigner', 'PySide6.QtUiTools',
    'PySide6.QtNetworkAuth', 'PySide6.QtOAuth1', 'PySide6.QtPrintSupport',
    # Python 标准库中不需要的（注意：urllib/email/http 被 inspect/pathlib 等内部依赖，不能删）
    'tkinter', 'unittest', 'pydoc', 'lib2to3',
    'PySide6.QtNetwork',  # 我们不联网
]

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'cat.models.cat',
        'cat.models.catsprite',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=_EXCLUDE_MODULES,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DesktopCat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 无终端窗口
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='DesktopCat',
)

# macOS: 包装成 .app 应用包
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='DesktopCat.app',
        icon=None,
        bundle_identifier='com.zcode.desktopcat',
        info_plist={
            'CFBundleName': 'DesktopCat',
            'CFBundleDisplayName': '桌面宠物猫',
            'CFBundleVersion': '0.5.0',
            'CFBundleShortVersionString': '0.5.0',
            'NSHighResolutionCapable': True,
            'LSUIElement': True,  # 不在 Dock/任务栏显示
        },
    )

