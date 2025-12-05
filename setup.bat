@echo off
setlocal

REM === Base directory (where this .bat is) ===
set BASE_DIR=%~dp0

REM === Detect wheel file ===
for /f "delims=" %%f in ('dir /b "%BASE_DIR%hyloa-*.whl" 2^>nul') do set WHEEL_FILE=%BASE_DIR%%%f

if not defined WHEEL_FILE (
    echo ERROR: No wheel file found in this folder.
    echo Place setup.bat and hyloa-xxx.whl in the same folder.
    pause
    exit /b 1
)

echo Found wheel: %WHEEL_FILE%

REM === Virtual environment path ===
set VENV_DIR=%BASE_DIR%venv
python -m venv "%VENV_DIR%"

REM === Install wheel ===
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_DIR%\Scripts\python.exe" -m pip install "%WHEEL_FILE%"

REM === Locate installed package (inside venv) ===
set SITE_PKGS=%VENV_DIR%\Lib\site-packages\hyloa

REM === Icon inside the installed package ===
set ICON_PATH=%SITE_PKGS%\resources\icon.ico

REM === Script vytvořený setuptools ===
set APP_EXE=%VENV_DIR%\Scripts\hyloa.exe

IF NOT EXIST "%APP_EXE%" (
    echo ERROR: hyloa.exe not found. Entry point missing.
    pause
    exit /b 1
)

REM === Create VBS launcher (no terminal) ===
set LAUNCH_VBS=%BASE_DIR%launch_hyloa.vbs

echo Set shell = CreateObject("WScript.Shell") > "%LAUNCH_VBS%"
echo shell.Run Chr(34) ^& "%APP_EXE%" ^& Chr(34), 0 >> "%LAUNCH_VBS%"
echo Set shell = Nothing >> "%LAUNCH_VBS%"

REM === Create desktop shortcut ===
set SHORTCUT=%USERPROFILE%\Desktop\hyloa.lnk

echo Set oWS = WScript.CreateObject("WScript.Shell") > temp.vbs
echo Set oLink = oWS.CreateShortcut("%SHORTCUT%") >> temp.vbs
echo oLink.TargetPath = "%LAUNCH_VBS%" >> temp.vbs
echo oLink.IconLocation = "%ICON_PATH%" >> temp.vbs
echo oLink.Description = "Start HYLOA" >> temp.vbs
echo oLink.WorkingDirectory = "%BASE_DIR%" >> temp.vbs
echo oLink.Save >> temp.vbs

cscript //nologo temp.vbs
del temp.vbs

echo ================================
echo Installation complete!
echo You can now run the application by double-clicking the shortcut on your Desktop.
pause
