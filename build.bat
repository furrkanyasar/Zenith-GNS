@echo off
echo.
echo === Zenith GNS Build Script ===
echo.

REM 1. Python kontrolü
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

echo HATA: Python bulunamadi! Lutfen Python'un yuklu oldugundan emin olun.
pause
exit /b 1

:found_python
echo Python komutu bulundu: %PY_CMD%

REM 2. venv kontrolü
if exist "venv\Scripts\python.exe" goto :start_build

echo Sanal ortam (venv) bulunamadi, olusturuluyor...
if exist venv rmdir /s /q venv
%PY_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo HATA: venv olusturulamadi!
    pause
    exit /b 1
)
echo Kutuphaneler yukleniyor...
call venv\Scripts\python.exe -m pip install --upgrade pip
call venv\Scripts\pip.exe install -r requirements.txt

:start_build
echo.
echo PyInstaller kontrol ediliyor...
call venv\Scripts\pip.exe install pyinstaller

echo.
echo Zenith GNS insa ediliyor (EXE yapiliyor)...
call venv\Scripts\pyinstaller.exe --noconfirm --onefile --windowed --icon "app_icon.ico" --name "Zenith GNS" --add-data "venv/Lib/site-packages/customtkinter;customtkinter/" --add-data "app_icon.ico;." main.py

if %errorlevel% neq 0 (
    echo.
    echo HATA: Build basarisiz oldu!
    pause
    exit /b 1
)

echo.
echo Islem tamam! EXE dosyaniz 'dist/Zenith GNS' klasorunun icinde.
pause
