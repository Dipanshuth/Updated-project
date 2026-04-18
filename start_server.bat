@echo off
echo ============================================
echo   AI Digital Memory Vault - Server Startup
echo ============================================
echo.

cd /d "%~dp0backend"

echo Checking Python installation...
py --version 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo Installing dependencies...
py -m pip install -q fastapi uvicorn sqlalchemy python-multipart pydantic

echo.
echo Starting backend server on http://localhost:8000 ...
echo Open http://localhost:8000 in your browser to access the app.
echo Press Ctrl+C to stop the server.
echo.

py -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
