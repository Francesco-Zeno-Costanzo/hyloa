@echo off
setlocal EnableDelayedExpansion

echo.
echo =========================================
echo            HYLOA INSTALLER
echo =========================================
echo.

REM -----------------------------------------
REM Directories
REM -----------------------------------------

set INSTALL_DIR=%LOCALAPPDATA%\Hyloa
set VENV_DIR=%INSTALL_DIR%\venv

mkdir "%INSTALL_DIR%" 2>nul

if exist "%VENV_DIR%" (
    echo Existing installation found.
    echo Removing old virtual environment...
    rmdir /s /q "%VENV_DIR%"
)

REM -----------------------------------------
REM Check Python and create virtual environment
REM -----------------------------------------

where python >nul 2>&1

if errorlevel 1 (
    echo Python not found.
    echo Please install Python 3.10 or higher and try again.
    pause
    exit /b 1
)

echo Creating virtual environment...

python -m venv "%VENV_DIR%"

if errorlevel 1 (
    echo Error creating virtual environment.
    pause
    exit /b 1
)

echo.
echo Updating pip...

"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip

echo.
echo Installing HYLOA...

set BASE_DIR=%~dp0

REM -----------------------------------------
REM Detect wheel file
REM -----------------------------------------

for /f "delims=" %%f in ('dir /b "%BASE_DIR%hyloa-*.whl" 2^>nul') do set WHEEL_FILE=%BASE_DIR%%%f

if not defined WHEEL_FILE (
    echo ERROR: No wheel file found in this folder.
    echo Place setup.bat and hyloa-xxx.whl in the same folder.
    pause
    exit /b 1
)

echo Found wheel: %WHEEL_FILE%

"%VENV_DIR%\Scripts\python.exe" -m pip install "%WHEEL_FILE%"

if errorlevel 1 (
    echo Error installing HYLOA.
    pause
    exit /b 1
)

REM -----------------------------------------
REM Paths
REM -----------------------------------------

set APP_EXE=%VENV_DIR%\Scripts\hyloa.exe
set ICON_FILE=%VENV_DIR%\Lib\site-packages\hyloa\resources\icon.ico

REM -----------------------------------------
REM Shortcut Desktop
REM -----------------------------------------

set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=%DESKTOP%\HYLOA.lnk

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut("%SHORTCUT%") >> "%TEMP%\create_shortcut.vbs"
echo oLink.TargetPath = "%APP_EXE%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.IconLocation = "%ICON_FILE%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Description = "HYLOA" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Save >> "%TEMP%\create_shortcut.vbs"

cscript //nologo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"

echo.
echo =========================================
echo Installation complete!
echo.
echo Virtual environment:
echo %VENV_DIR%
echo.
echo Executable:
echo %APP_EXE%
echo.
echo Shortcut created on Desktop.
echo You can now run the application by double-clicking the shortcut on your Desktop.
echo =========================================

pause
