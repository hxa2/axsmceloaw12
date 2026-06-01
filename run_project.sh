#!/bin/bash

# run_project.sh
# Kịch bản khởi động cho macOS và Linux

echo "======================================================================="
echo "         KHOI DONG DU AN BAI TOAN VAN TAI (TRANSPORTATION SOLVER)      "
echo "======================================================================="

# 1. Check Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Khong tim thay Python trong he thong!"
    echo "Vui long cai dat Python 3.10+ (macOS/Linux)."
    exit 1
fi

# 2. Check Node.js
if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
    echo "[ERROR] Khong tim thay Node.js hoac npm trong he thong!"
    echo "Vui long cai dat Node.js 20+ de chay frontend."
    exit 1
fi

echo "[OK] Da kiem tra he thong:"
echo "  - Python: San sang ($PYTHON_CMD)"
echo "  - Node.js: San sang"
echo ""

# 3. Setup Backend
echo "[1/2] Dang kiem tra va cai dat moi truong Backend..."
cd backend || exit
if [ ! -d ".venv" ]; then
    echo "  - Dang tao virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

echo "  - Dang cap nhat pip va cai dat thu vien Python (vui long doi)..."
source .venv/bin/activate
pip install --upgrade pip >/dev/null 2>&1
pip install -r requirements.txt
cd ..

echo ""
# 4. Setup Frontend
echo "[2/2] Dang kiem tra va cai dat moi truong Frontend..."
cd frontend || exit
echo "  - Dang cai dat cac thu vien Node.js (vui long doi)..."
npm install
cd ..

echo ""
echo "======================================================================="
echo " Hoan tat cai dat! Dang khoi dong cac server..."
echo "======================================================================="
echo ""

# Start servers
cd backend && source .venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd frontend && npm run dev -- --host &
FRONTEND_PID=$!

echo " * Backend API dang chay tai:  http://localhost:8000"
echo " * Swagger UI (API Docs):      http://localhost:8000/docs"
echo " * Frontend React dang chay tai: http://localhost:5173"
echo ""
echo " De truy cap tu thiet bi khac trong cung mang LAN, hay su dung IP cua may tinh nay."
echo " An [Ctrl+C] de tat ca 2 server."
echo "======================================================================="

# Bắt sự kiện Ctrl+C để kill cả 2 process
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
