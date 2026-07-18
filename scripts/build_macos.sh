#!/usr/bin/env bash
# macOS 一键打包脚本：打包 → 瘦身 → 签名
# 产出：dist/DesktopCat.app（双击即可启动，无需 Python）
set -e
cd "$(dirname "$0")/.."

echo "=== 1/4 清理旧产物 ==="
rm -rf build dist

echo "=== 2/4 PyInstaller 打包 ==="
python3 -m PyInstaller desktop-cat.spec --noconfirm

echo "=== 3/4 瘦身（删除无用 Qt 模块）==="
python3 scripts/strip_app.py

echo "=== 4/4 重新签名 ==="
codesign --force --deep --sign - dist/DesktopCat.app

echo ""
echo "✅ 打包完成！"
du -sh dist/DesktopCat.app
echo ""
echo "双击启动：open dist/DesktopCat.app"
echo "或把 dist/DesktopCat.app 拖到「应用程序」文件夹即可像普通 App 使用。"
