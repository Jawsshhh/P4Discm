@echo off
REM ================================
REM Activate virtual environment
REM ================================
call venv\Scripts\activate.bat

REM ================================
REM Start Training Server (new window)
REM ================================
echo Starting Training Server...
start "Training Server" cmd /k python server\training_server.py

REM ================================
REM Wait for server to initialize
REM ================================
echo Waiting for server to load CIFAR-10 dataset...
timeout /t 5 /nobreak

REM ================================
REM Start Web Dashboard Client (new window)
REM ================================
echo Starting Web Dashboard...
start "Web Dashboard" cmd /k python client\web_dashboard.py

echo.
echo ========================================
echo Both applications started!
echo Open http://localhost:5000 in browser
echo ========================================
pause