@echo off
setlocal

REM === Nome della cartella del progetto ===
set PROJECT_NAME=hyloa

REM === Percorso assoluto di questa cartella ===
set BASE_DIR=%~dp0

REM === Percorso ambiente virtuale ===
set VENV_DIR=%BASE_DIR%venv

REM === Percorso a Python dentro l'ambiente virtuale ===
set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe

REM === Percorso allo script main ===
set MAIN_SCRIPT=%BASE_DIR%hyloa\main.py

REM === Percorso alla shortcut da creare sul Desktop ===
set SHORTCUT_NAME=hyloa.lnk
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_PATH=%DESKTOP%\%SHORTCUT_NAME%

REM === Percorso all'icona del pacchetto ===
set ICON_PATH=%BASE_DIR%hyloa\resources\icon.ico

REM === Percorso al launcher VBS ===
set LAUNCH_VBS=%BASE_DIR%launch_hyloa.vbs

echo ================================
echo Creazione ambiente virtuale...
python -m venv "%VENV_DIR%"

echo ================================
echo Attivazione ambiente virtuale...
call "%VENV_DIR%\Scripts\activate.bat"

echo ================================
echo Installazione dipendenze...
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install -r requirements.txt
"%PYTHON_EXE%" -m pip install .

echo ================================
echo Creazione script VBS di avvio...
REM === Salva un file .vbs che avvia il programma senza mostrare il terminale
echo Set WshShell = CreateObject("WScript.Shell") > "%LAUNCH_VBS%"
echo WshShell.Run Chr(34) ^& "%PYTHON_EXE%" ^& Chr(34) ^& " " ^& Chr(34) ^& "%MAIN_SCRIPT%" ^& Chr(34), 0 >> "%LAUNCH_VBS%"
echo Set WshShell = Nothing >> "%LAUNCH_VBS%"

echo ================================
echo Creazione shortcut sul Desktop...

REM === Crea la scorciatoia alla VBS
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
echo Installazione completata!
echo Scorciatoia creata sul Desktop.
pause
