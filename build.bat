@echo off
echo Installing PyInstaller...
call venv\Scripts\pip.exe install pyinstaller

echo.
echo Building Zenith GNS...
REM Pyinstaller compile command specifically configured for CustomTkinter
REM --noconsole prevents the black cmd window from showing behind the UI
REM --icon specifies the app_icon.ico
REM --name sets the generated executable name
call venv\Scripts\pyinstaller.exe ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --icon "app_icon.ico" ^
    --name "Zenith GNS" ^
    --add-data "venv/Lib/site-packages/customtkinter;customtkinter/" ^
    --add-data "app_icon.ico;." ^
    main.py

echo.
echo Build complete! Your executable is inside the 'dist\Zenith GNS' folder.
pause
