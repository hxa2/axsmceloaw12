@echo off
:: Set terminal window title and colors
title Khoi dong Du an Bai toan Van tai - Transportation Solver
color 0F

echo =======================================================================
echo          KHOI DONG DU AN BAI TOAN VAN TAI (TRANSPORTATION SOLVER)
echo =======================================================================

:: 1. Check Python
set PYTHON_CMD=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Khong tim thay Python trong he thong!
        echo Vui long tai va cai dat Python 3.10+ - nho tich chon "Add Python to PATH".
        echo Link tai: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
)

:: 2. Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Khong tim thay Node.js - npm trong he thong!
    echo Vui long tai va cai dat Node.js 20+ de chay frontend.
    echo Link tai: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo [OK] Da kiem tra he thong:
echo   - Python: San sang (%PYTHON_CMD%)
echo   - Node.js: San sang
echo.
echo [1/2] Dang kiem tra va cai dat moi truong Backend...
cd backend
if not exist .venv (
    echo - Dang tao virtual environment...
    %PYTHON_CMD% -m venv .venv
)
echo - Dang cap nhat pip va cai dat cac thu vien Python (vui long doi)...
.venv\Scripts\python -m pip install --upgrade pip >nul 2>nul
.venv\Scripts\python -m pip install -r requirements.txt
cd ..

echo.
echo [2/2] Dang kiem tra va cai dat moi truong Frontend...
cd frontend
echo - Dang cai dat cac thu vien Node.js (vui long doi)...
call npm install
cd ..

echo.
echo =======================================================================
echo  Hoan tat cai dat! Dang khoi dong cac server...
echo =======================================================================
echo.

:: Khoi dong Backend
start "Backend Server - FastAPI" cmd /k "title Backend Server - FastAPI && echo Dang chay Backend... && backend\.venv\Scripts\python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Khoi dong Frontend 
start "Frontend Server - Vite" cmd /k "title Frontend Server - Vite && cd frontend && echo Dang chay Frontend... && npm run dev -- --host"

echo  * Backend API dang chay tai:  http://localhost:8000
echo  * Swagger UI (API Docs):      http://localhost:8000/docs
echo  * Frontend React dang chay tai: http://localhost:5173
echo.
echo  De truy cap tu thiet bi khac trong cung mang LAN, hay su dung IP cua may tinh nay.
echo  Moi thay doi tren ma nguon se tu dong duoc cap nhat (Hot Reload).
echo =======================================================================
echo.
echo Nhan phim bat ky de dong cua so trinh dieu khien nay (2 cua so server van tiep tuc chay).
pause >nul
