@echo off
REM
REM QFNU Empty Classrooms - Windows Debug Script (Single Instance)
REM

setlocal EnableDelayedExpansion

title QFNU Empty Classrooms - Debug Mode

echo ========================================
echo    QFNU Empty Classrooms Service
echo         Debug Mode (Windows)
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check for existing instance
echo [1/5] Checking for existing instance...
set "LOCK_FILE=%TEMP%\qfnu-empty-classrooms.lock"

if exist "%LOCK_FILE%" (
    set /p EXISTING_PID=<"%LOCK_FILE%"

    REM Check if the process is still running
    tasklist /FI "PID eq !EXISTING_PID!" 2>nul | find /i "python" >nul
    if !errorlevel! equ 0 (
        echo   [WARNING] Another instance is already running ^(PID: !EXISTING_PID!^)
        echo.
        choice /C YN /M "Do you want to stop the existing instance and start a new one"
        if !errorlevel! equ 1 (
            echo   Stopping existing instance...
            taskkill /PID !EXISTING_PID! /F >nul 2>&1
            timeout /t 2 /nobreak >nul
        ) else (
            echo   Exiting...
            exit /b 0
        )
    ) else (
        echo   Stale lock file found, cleaning up...
        del "%LOCK_FILE%" >nul 2>&1
    )
)
echo   [OK] No conflicting instance found
echo.

REM Check Python
echo [2/5] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo   [OK] Python version: %PYTHON_VERSION%
echo.

REM Check virtual environment
echo [3/5] Checking virtual environment...
if exist ".venv\Scripts\activate.bat" (
    echo   [OK] Virtual environment found
    call .venv\Scripts\activate.bat
) else (
    echo   Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo   [OK] Virtual environment created
)
echo.

REM Install dependencies
echo [4/5] Installing dependencies...
where uv >nul 2>&1
if %errorlevel% equ 0 (
    echo   Using uv for package management
    uv sync --quiet
) else (
    echo   Using pip for package management
    pip install -q -e .
)
echo   [OK] Dependencies installed
echo.

REM Check .env
echo [5/5] Checking configuration...
if not exist ".env" (
    if exist ".env.example" (
        echo   .env not found, copying from .env.example
        copy .env.example .env >nul
        echo   [WARNING] Please edit .env file with your credentials
        notepad .env
        pause
    ) else (
        echo   [ERROR] .env file not found
        pause
        exit /b 1
    )
)
echo   [OK] Configuration loaded
echo.

REM Create lock file with PID
REM We need to get the PID after starting Python, so we use a workaround
echo ========================================
echo   Starting Flask Development Server
echo   URL: http://127.0.0.1:5000
echo   Press Ctrl+C to stop
echo ========================================
echo.

REM Set Flask debug mode
set FLASK_DEBUG=1

REM Start Python and save PID
for /f "tokens=2" %%a in ('wmic process call create "cmd /c cd /d %~dp0 && .venv\Scripts\python.exe app.py" ^| find "ProcessId"') do (
    set "PID=%%a"
)

REM Fallback: run directly if wmic method fails
if not defined PID (
    REM Create a simple lock indicator
    echo %date% %time% > "%LOCK_FILE%"

    REM Run directly
    python app.py

    REM Cleanup on exit
    del "%LOCK_FILE%" >nul 2>&1
) else (
    set "PID=!PID:;=!"
    echo !PID! > "%LOCK_FILE%"

    REM Wait for the process
    echo Server started with PID: !PID!
    echo.

    :wait_loop
    timeout /t 5 /nobreak >nul
    tasklist /FI "PID eq !PID!" 2>nul | find /i "python" >nul
    if !errorlevel! equ 0 goto wait_loop

    REM Cleanup
    del "%LOCK_FILE%" >nul 2>&1
)

echo.
echo Server stopped.
pause
