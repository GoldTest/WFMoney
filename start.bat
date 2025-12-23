@echo off
setlocal

echo ==========================================
echo    EasyMoney AI - Windows Launcher
echo ==========================================
echo.

:: 1. Check Python
echo [1/4] Checking Python environment...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

:: 2. Install dependencies
echo [2/4] Installing/Updating dependencies...
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Dependency installation failed. Please check your internet.
)

:: 3. Start Backend
echo [3/4] Starting Backend (Port 8000)...
start "EasyMoney_Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

:: 4. Start Frontend
echo [4/4] Starting Frontend (Port 8080)...
start "EasyMoney_Frontend" cmd /k "cd frontend && python -m http.server 8080"

echo.
echo ==========================================
echo    Application Started Successfully!
echo.
echo    Backend: http://localhost:8000
echo    Frontend: http://localhost:8080
echo.
echo    Please do not close the command windows.
echo ==========================================
echo.

:: 5. Open Browser
timeout /t 5 /nobreak >nul
start http://localhost:8080

pause
