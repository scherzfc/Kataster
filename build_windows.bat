@echo off
REM Kataster-Sorter Windows Build Script
REM Dieses Script erstellt die Windows-Installer

echo ========================================
echo    Kataster-Sorter Build (Windows)
echo ========================================
echo.

REM Prüfen ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte installiere Python von: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Virtual Environment erstellen
if not exist "venv" (
    echo [1/4] Erstelle virtuelle Umgebung...
    python -m venv venv
)

REM Aktivieren und Dependencies installieren
echo [2/4] Installiere Abhängigkeiten...
call venv\Scripts\activate.bat
pip install -r requirements.txt pyinstaller --quiet

REM PyInstaller ausführen
echo [3/4] Erstelle Executable...
pyinstaller --onefile --windowed --name "Kataster-Sorter" ^
    --add-data "pdf_processor.py;." ^
    --hidden-import customtkinter ^
    --collect-all customtkinter ^
    --icon icon.ico ^
    desktop_app.py

echo [4/4] Fertig!
echo.
echo Die Executable liegt in: dist\Kataster-Sorter.exe
echo.
pause
