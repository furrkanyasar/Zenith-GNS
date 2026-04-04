@echo off
echo.
echo === Zenith GNS Build Script ===
echo.

REM 1. Check for Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :found_python
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
    goto :found_python
)

echo ERROR: Python not found! Please ensure Python is installed.
pause
exit /b 1

:found_python
echo Python command found: %PY_CMD%

REM 2. Check for venv
if exist "venv\Scripts\python.exe" goto :start_build

echo Virtual environment (venv) not found, creating...
if exist venv rmdir /s /q venv
%PY_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create venv!
    pause
    exit /b 1
)
echo Installing dependencies...
call venv\Scripts\python.exe -m pip install --upgrade pip
call venv\Scripts\pip.exe install -r requirements.txt

:start_build
echo.
echo Checking PyInstaller...
call venv\Scripts\pip.exe install pyinstaller

echo.
echo Building Zenith GNS (creating EXE)...
call venv\Scripts\pyinstaller.exe --noconfirm --onefile --windowed --icon "app_icon.ico" --name "Zenith GNS" --add-data "venv/Lib/site-packages/customtkinter;customtkinter/" --add-data "app_icon.ico;." --add-data "assets;assets" main.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Build complete! The EXE file is located in the 'dist/' folder.
pause
