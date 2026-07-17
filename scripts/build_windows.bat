@echo off
REM Windows 一键打包脚本：打包 → 瘦身
REM 产出：dist\DesktopCat\DesktopCat.exe（双击即可启动，无需 Python）
REM 必须在 Windows 上运行（不能在 Mac 上跑这个）
setlocal
cd /d "%~dp0\.."

echo === 1/3 清理旧产物 ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo === 2/3 PyInstaller 打包 ===
python -m PyInstaller desktop-cat.spec --noconfirm
if errorlevel 1 (
    echo 打包失败
    exit /b 1
)

echo === 3/3 瘦身（删除无用 Qt 模块）===
python scripts\strip_app.py win
if errorlevel 1 (
    echo 瘦身失败
    exit /b 1
)

echo.
echo === 打包完成！ ===
dir dist\DesktopCat\DesktopCat.exe
echo.
echo 双击启动：dist\DesktopCat\DesktopCat.exe
echo 可把 dist\DesktopCat 整个文件夹压缩后分发。
endlocal
