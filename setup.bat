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

echo ================================
echo Creation of virtual environment...
python -m venv "%VENV_DIR%"

echo ================================
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo ================================
echo Installing dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install -r requirements.txt
"%PYTHON_EXE%" -m pip install .

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
