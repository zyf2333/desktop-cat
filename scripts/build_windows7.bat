@echo off
REM Windows 7 SP1 x64 build: Python 3.8 + PySide2/Qt5.
setlocal
cd /d "%~dp0\.."
set DESKTOP_CAT_QT_API=pyside2

python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 8) else 1)"
if errorlevel 1 (
    echo ERROR: activate a Python 3.8 virtual environment first.
    echo Example: .venv38\Scripts\activate
    exit /b 1
)

python -c "import PySide2, PyInstaller; print('Qt binding:', PySide2.__version__)"
if errorlevel 1 (
    echo ERROR: install dependencies with requirements-win7.txt first.
    exit /b 1
)

echo === 1/3 Clean old artifacts ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo === 2/3 Build with Python 3.8 and Qt 5 ===
python -m PyInstaller desktop-cat.spec --noconfirm --clean
if errorlevel 1 exit /b 1

echo === 3/3 Remove unused Qt modules ===
python scripts\strip_app.py win
if errorlevel 1 exit /b 1

echo.
echo Windows 7 build completed: dist\DesktopCat\DesktopCat.exe
echo Distribute the entire dist\DesktopCat directory.
endlocal
