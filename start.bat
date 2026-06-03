@echo off
echo ============================================
echo   Conga CPQ AI Agent - Starting Up
echo ============================================

cd /d "%~dp0"

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python from https://python.org
    pause
    exit /b 1
)

echo.
echo [1/2] Installing dependencies...
python -m pip install -r backend\requirements.txt
python -m pip install streamlit simple-salesforce

echo.
echo [2/2] Starting Streamlit app on http://localhost:8501
echo.
python -m streamlit run app.py --server.port 8501

pause
