@echo off

setlocal enabledelayedexpansion

:: Set console title and colors
title Enrollware Automation - Running Application
color 0A

echo ==========================================
echo    ENROLLWARE AUTOMATION RUNNER
echo ==========================================
echo.

:: Check if setup was completed
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run 'setup.bat' first to install dependencies
    pause
    exit /b 1
)

:: Check if main.py exists
if not exist "main.py" (
    echo [ERROR] main.py not found in current directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    echo Please run 'setup.bat' to fix the environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

:: Create logs directory if it doesn't exist
if not exist "logs\" (
    mkdir logs
    echo [INFO] Created logs directory
)

:: Set log file with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"
set "logfile=logs\run_%timestamp%.log"

:: Start the application
echo.
echo ==========================================
echo    STARTING ENROLLWARE AUTOMATION
echo ==========================================
echo.
echo [INFO] Starting application...
echo [INFO] Log file: %logfile%
echo [INFO] Press Ctrl+C to stop the application
echo.
echo ==========================================

:: Initialize log file with header
echo [%date% %time%] Starting Enrollware Automation > "%logfile%"
echo [%date% %time%] Current directory: %CD% >> "%logfile%"
echo [%date% %time%] ========================================== >> "%logfile%"

:: Run Python script with simple logging that shows output in terminal
echo Running: python main.py
echo.

:: Simple approach: run python and capture output to both console and log
python main.py 2>&1 | (
    for /f "delims=" %%i in ('more') do (
        echo %%i
        echo [%date% %time%] %%i >> "%logfile%"
    )
)

set SCRIPT_EXIT_CODE=%errorlevel%

:: Add completion status to log
echo. >> "%logfile%"
echo [%date% %time%] ========================================== >> "%logfile%"

echo.
echo ==========================================
if %SCRIPT_EXIT_CODE% equ 0 (
    echo [SUCCESS] Application completed successfully
    echo [%date% %time%] Application completed successfully with exit code: %SCRIPT_EXIT_CODE% >> "%logfile%"
    color 0A
) else (
    echo [ERROR] Application exited with error code: %SCRIPT_EXIT_CODE%
    echo [%date% %time%] Application exited with error code: %SCRIPT_EXIT_CODE% >> "%logfile%"
    color 0C
)
echo ==========================================
echo.
echo Log file saved: %logfile%
echo.

set /p view_log="View log file? (y/N): "
if /i "!view_log!" equ "y" (
    if exist "%logfile%" (
        start notepad "%logfile%"
    )
)

echo Press any key to exit...
pause >nul

:: Deactivate virtual environment
call deactivate >nul 2>&1

exit /b %SCRIPT_EXIT_CODE%
