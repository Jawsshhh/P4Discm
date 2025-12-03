@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo =========================================
echo Python gRPC Project Setup + Build Script
echo =========================================


REM ---------- Step 2: Create virtual environment ----------
IF NOT EXIST venv (
    echo [2/6] Creating virtual environment...
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
) ELSE (
    echo [2/6] Virtual environment already exists.
)

REM ---------- Step 3: Activate virtual environment ----------
echo [3/6] Activating virtual environment...
call venv\Scripts\activate
IF ERRORLEVEL 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM ---------- Step 4: Upgrade pip ----------
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip

REM ---------- Step 5: Install dependencies ----------
echo [5/6] Installing dependencies...
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

REM ---------- Step 6: Compile proto files ----------
IF EXIST proto_compile.bat (
    echo [6/6] Compiling proto files...
    call proto_compile.bat
    IF ERRORLEVEL 1 (
        echo ERROR: Proto compilation failed.
        pause
        exit /b 1
    )
) ELSE (
    echo proto_compile.bat not found. Skipping.
)

REM ---------- Step 7: Build executables ----------
echo =========================================
echo Building executables with PyInstaller
echo =========================================

IF EXIST training_server.spec (
    echo Building training_server.exe...
    pyinstaller training_server.spec
) ELSE (
    echo WARNING: training_server.spec not found.
)

IF EXIST dashboard_client.spec (
    echo Building dashboard_client.exe...
    pyinstaller dashboard_client.spec
) ELSE (
    echo WARNING: dashboard_client.spec not found.
)

echo =========================================
echo ✅ Setup and Build Complete
echo =========================================

pause
ENDLOCAL
