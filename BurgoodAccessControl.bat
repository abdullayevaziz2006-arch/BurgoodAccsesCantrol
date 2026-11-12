@echo off
title Burgood Access Control
echo ===================================================
echo    BURGOOD ACCESS CONTROL - ISHGA TUSHMOQDA...
echo ===================================================
cd /d "%~dp0"

echo 1. Markaziy Server va Telegram Botlar tekshirilmoqda...
powershell -Command "try { $res = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/' -TimeoutSec 1; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    Server fonda ishga tushirilmoqda...
    start /min "" python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    timeout /t 2 >nul
)

echo 2. Frontend tekshirilmoqda...
powershell -Command "try { $res = Invoke-RestMethod -Uri 'http://127.0.0.1:3000/' -TimeoutSec 1; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    Frontend fonda ishga tushirilmoqda...
    cd frontend
    start /min "" npm run dev -- --host 127.0.0.1 --port 3000
    cd ..
    timeout /t 2 >nul
)

echo 3. Desktop Oyna ochilmoqda...
start "" python backend/desktop_app.py
exit
