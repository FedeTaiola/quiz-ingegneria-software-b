@echo off
REM ============================================================
REM avvia_windows.bat — Avvia il quiz (Windows)
REM ============================================================
REM Fai doppio click su questo file per avviare il quiz.
REM Il browser si aprira' automaticamente.
REM ============================================================

cd /d "%~dp0"

echo.
echo === Database Crocette - Ing. Software B ===
echo.

REM Controlla se Python e' installato
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato.
    echo Scaricalo da https://www.python.org/downloads/ e assicurati
    echo di spuntare "Add Python to PATH" durante l'installazione.
    pause
    exit /b 1
)

REM Installa le dipendenze se mancanti
echo Controllo dipendenze...
python -m pip install --quiet -r requirements.txt

echo Avvio del server...
echo Il browser si aprira' su http://localhost:5000
echo Premi CTRL+C o chiudi questa finestra per fermare il server.
echo.

python app.py

pause
