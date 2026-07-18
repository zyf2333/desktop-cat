# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置（macOS / Windows 通用）。

打包产出 dist/DesktopCat.app（macOS）或 dist/DesktopCat/DesktopCat.exe（Windows）。
用户双击即可启动，无需安装 Python 或依赖。

用法：
    pyinstaller desktop-cat.spec --noconfirm

macOS 产出：dist/DesktopCat.app（双击启动）
Windows 产出：dist/DesktopCat/DesktopCat.exe（双击启动）
"""
import os
import sys

block_cipher = None

# 把 assets/ 目录（精灵素材）作为数据文件打进包
datas = [
    ('assets', 'assets'),
]

# Windows 7 构建显式选择 PySide2，现代构建默认使用 PySide6。
_QT_API = os.environ.get('DESKTOP_CAT_QT_API', '').strip().lower()
if _QT_API == 'pyside2':
    _QT_PACKAGE = 'PySide2'
elif _QT_API in ('', 'pyside6'):
    _QT_PACKAGE = 'PySide6'
else:
    raise RuntimeError(f'Unsupported DESKTOP_CAT_QT_API: {_QT_API}')
_INACTIVE_QT_PACKAGE = 'PySide2' if _QT_PACKAGE == 'PySide6' else 'PySide6'

# 排除的 Qt 模块（我们只用 QtCore/QtGui/QtWidgets，其他全删）
# 这些是体积大头：QtWebEngineCore 单独就 216MB
_EXCLUDE_QT_MODULES = [
    # 3D 相关（已移除的功能）
    'Qt3DCore', 'Qt3DAnimation', 'Qt3DExtras',
    'Qt3DInput', 'Qt3DLogic', 'Qt3DRender',
    # WebEngine（浏览器引擎，216MB，我们不用）
    'QtWebEngineCore', 'QtWebEngineWidgets', 'QtWebEngineQuick',
    'QtWebChannel', 'QtWebSockets',
    # Quick/QML（ declarative UI，不用）
    'QtQuick', 'QtQuick3D', 'QtQuickControls2', 'QtQuickWidgets',
    'QtQuickTest', 'QtQml',
    # 多媒体/图表/数据可视化（不用）
    'QtMultimedia', 'QtMultimediaWidgets', 'QtCharts',
    'QtDataVisualization', 'QtPdf', 'QtPdfWidgets', 'QtSpatialAudio',
    'QtTextToSpeech', 'QtBluetooth', 'QtNfc', 'QtPositioning',
    'QtLocation', 'QtSensors', 'QtSerialPort', 'QtSerialBus',
    'QtRemoteObjects', 'QtScxml', 'QtStateMachine', 'QtSql', 'QtTest',
    'QtHelp', 'QtDesigner', 'QtUiTools', 'QtNetworkAuth', 'QtOAuth1',
    'QtPrintSupport', 'QtNetwork',
]

_EXCLUDE_MODULES = [
    f'{_QT_PACKAGE}.{module}' for module in _EXCLUDE_QT_MODULES
] + [
    # Python 标准库中不需要的（注意：urllib/email/http 被 inspect/pathlib 等内部依赖，不能删）
    'tkinter', 'unittest', 'pydoc', 'lib2to3',
    _INACTIVE_QT_PACKAGE,
]

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'cat.qt',
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
