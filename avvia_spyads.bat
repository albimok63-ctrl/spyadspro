@echo off
title 🚀 Avvio SpyAds Pro

echo ===============================
echo      SPYADS PRO - LAUNCHER
echo ===============================
echo.

REM === Avvio Backend (FastAPI) ===
echo [1/2] Avvio backend FastAPI...
cd /d "C:\Users\albim\OneDrive\Desktop\spyads_pro\backend"
start cmd /k "python -m uvicorn main:app --reload"
timeout /t 5 >nul

REM === Avvio Frontend (Streamlit) ===
echo [2/2] Avvio frontend Streamlit...
cd /d "C:\Users\albim\OneDrive\Desktop\spyads_pro\frontend"
start cmd /k "streamlit run app.py"

echo.
echo ✅ SpyAds Pro è ora in esecuzione!
echo 🌐 Backend  →  http://127.0.0.1:8000
echo 🖥️ Frontend →  http://localhost:8501
echo.
pause