@echo off
setlocal

REM === Project folder name ===
set PROJECT_NAME=hyloa

REM === Absolute path of this folder ===
set BASE_DIR=%~dp0

REM === Virtual environment path ===
set VENV_DIR=%BASE_DIR%venv

REM === Path to Python within the virtual environment ===
set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe

REM === Path to the main script ===
set MAIN_SCRIPT=%BASE_DIR%hyloa\main.py

REM === Path to the shortcut to create on the Desktop ===
set SHORTCUT_NAME=hyloa.lnk
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_PATH=%DESKTOP%\%SHORTCUT_NAME%

REM === Path to the package icon ===
set ICON_PATH=%BASE_DIR%hyloa\resources\icon.ico

REM === Path to the VBS launcher ===
set LAUNCH_VBS=%BASE_DIR%launch_hyloa.vbs

REM === Path to the wheel file (assumed inside dist\) ===
for /f "delims=" %%f in ('dir /b "%BASE_DIR%dist\hyloa-*.whl" 2^>nul') do set WHEEL_FILE=%BASE_DIR%dist\%%f

echo ================================
echo Checking for wheel package...
if not defined WHEEL_FILE (
    echo ERROR: No wheel found in dist\ folder.
    echo Please ensure a file like dist\hyloa-x.y.z-py3-none-any.whl exists.
    pause
    exit /b 1
)
echo Found: %WHEEL_FILE%

echo ================================
echo Creation of virtual environment...
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
)

echo ================================
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo ================================
echo Installing package from wheel...
"%PYTHON_EXE%" -m pip install --force-reinstall "%WHEEL_FILE%"

echo ================================
echo Creating VBS launcher...
REM === Save a .vbs file that launches the program without showing the terminal
echo Set WshShell = CreateObject("WScript.Shell") > "%LAUNCH_VBS%"
echo WshShell.Run Chr(34) ^& "%PYTHON_EXE%" ^& Chr(34) ^& " " ^& Chr(34) ^& "%MAIN_SCRIPT%" ^& Chr(34), 0 >> "%LAUNCH_VBS%"
echo Set WshShell = Nothing >> "%LAUNCH_VBS%"

echo ================================
echo Creating shortcut on Desktop...

REM === Create the shortcut to VBS
echo Set oWS = WScript.CreateObject("WScript.Shell") > temp.vbs
echo sLinkFile = "%SHORTCUT_PATH%" >> temp.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> temp.vbs
echo oLink.TargetPath = "%LAUNCH_VBS%" >> temp.vbs
echo oLink.WorkingDirectory = "%BASE_DIR%" >> temp.vbs
echo oLink.WindowStyle = 1 >> temp.vbs
echo oLink.IconLocation = "%ICON_PATH%" >> temp.vbs
echo oLink.Description = "Avvia hyloa GUI" >> temp.vbs
echo oLink.Save >> temp.vbs

cscript //nologo temp.vbs
del temp.vbs

echo ================================
echo Installation complete!
echo You can now run the application by double-clicking the shortcut on your Desktop.
pause
