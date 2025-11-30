@echo off
REM ================================
REM Activate virtual environment
REM ================================
call venv\Scripts\activate.bat

REM ================================
REM Start Training Server (new window)
REM ================================
start "Training Server" cmd /k python server\training_server.py

REM ================================
REM Start Web Dashboard Client (new window)
REM ================================
start "Web Dashboard" cmd /k python client\web_dashboard.py
