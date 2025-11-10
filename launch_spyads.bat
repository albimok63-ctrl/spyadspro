

@echo off
title SpyAds Pro - Avvio Automatico
echo ================================================
echo      AVVIO SPYADS PRO (Backend + Frontend)
echo ================================================

:: Avvio del backend (FastAPI)
echo [1/2] Avvio backend FastAPI su porta 8000...
start cmd /k "cd backend && python -m uvicorn main:app --reload"

:: Attesa 5 secondi per permettere al backend di partire
timeout /t 5 /nobreak >nul

:: Avvio del frontend (Streamlit)
echo [2/2] Avvio frontend Streamlit su porta 8501...
start cmd /k "cd frontend && streamlit run app.py"

echo ================================================
echo Tutti i servizi sono stati avviati correttamente.
echo Backend su: http://127.0.0.1:8000
echo Frontend su: http://localhost:8501
echo ================================================
pause