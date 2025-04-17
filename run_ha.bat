@echo off
setlocal

REM === Nome della cartella del progetto ===
set PROJECT_NAME=Hysteresis

REM === Percorso assoluto di questa cartella ===
set BASE_DIR=%~dp0

REM === Percorso ambiente virtuale ===
set VENV_DIR=%BASE_DIR%venv

REM === Percorso a Python dentro l'ambiente virtuale ===
set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe

REM === Percorso allo script main ===
set MAIN_SCRIPT=%BASE_DIR%Hysteresis\main.py

REM === Percorso alla shortcut da creare sul Desktop ===
set SHORTCUT_NAME=Avvia_Hysteresis.lnk
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_PATH=%DESKTOP%\%SHORTCUT_NAME%

echo ================================
echo Creazione ambiente virtuale...
python -m venv "%VENV_DIR%"

echo ================================
echo Attivazione ambiente virtuale...
call "%VENV_DIR%\Scripts\activate.bat"

echo ================================
echo Installazione dipendenze...
pip install --upgrade pip
pip install -r requirements.txt
pip install .

echo ================================
echo Creazione shortcut sul Desktop...

REM === VBS per creare shortcut ===
echo Set oWS = WScript.CreateObject("WScript.Shell") > temp.vbs
echo sLinkFile = "%SHORTCUT_PATH%" >> temp.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> temp.vbs
echo oLink.TargetPath = "%PYTHON_EXE%" >> temp.vbs
echo oLink.Arguments = """%MAIN_SCRIPT%""" >> temp.vbs
echo oLink.WorkingDirectory = "%BASE_DIR%" >> temp.vbs
echo oLink.WindowStyle = 1 >> temp.vbs
echo oLink.IconLocation = "%PYTHON_EXE%, 0" >> temp.vbs
echo oLink.Description = "Avvia Hysteresis GUI" >> temp.vbs
echo oLink.Save >> temp.vbs

REM === Esegui lo script VBS ===
cscript //nologo temp.vbs
del temp.vbs

echo ================================
echo Installazione completata!
echo Shortcut creata sul Desktop.
pause
