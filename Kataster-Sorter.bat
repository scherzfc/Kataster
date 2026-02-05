@echo off
title Kataster-Sorter
echo.
echo ========================================
echo    Kataster-Sorter wird gestartet...
echo ========================================
echo.

REM Prüfen ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte installiere Python von: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Prüfen ob venv existiert, sonst erstellen
if not exist "venv" (
    echo [INFO] Erstelle virtuelle Umgebung...
    python -m venv venv
    echo [INFO] Installiere Abhängigkeiten...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt --quiet
) else (
    call venv\Scripts\activate.bat
)

echo.
echo [OK] App startet im Browser...
echo [OK] Zum Beenden: Dieses Fenster schließen
echo.

REM Streamlit starten
streamlit run app.py --server.headless true --browser.gatherUsageStats false
