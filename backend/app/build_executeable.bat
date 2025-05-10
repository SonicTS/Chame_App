@echo off
REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Run PyInstaller to create the executable
pyinstaller --onefile --windowed ^
--add-data "..\..\frontend\admin_webpage\templates;templates" ^
--add-data "../../frontend/admin_webpage/static;static" ^
--collect-all chame_app ^
.\chame_app\__main__.py

REM Notify the user
echo Build complete. The executable is located in the "dist" folder.
pause