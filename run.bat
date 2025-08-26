@echo off

setlocal enabledelayedexpansion

:: Set console title and colors
title Enrollware Automation - Dependency Check and Runner
color 0A

echo ==========================================
echo    ENROLLWARE AUTOMATION RUNNER
echo ==========================================
echo.

:: Check if Python is installed
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

:: Check if pip is available
echo.
echo [2/7] Checking pip installation...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)
echo [OK] pip is available

:: Check if virtual environment exists
echo.
echo [3/7] Checking virtual environment...
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment found
)

:: Activate virtual environment
echo.
echo [4/7] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

:: Check and install requirements
echo.
echo [5/7] Checking dependencies...
if exist "requirements.txt" (
    echo [INFO] Installing/updating dependencies from requirements.txt...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed successfully
) else (
    echo [INFO] requirements.txt not found. Installing common dependencies...
    python -m pip install --upgrade pip selenium webdriver-manager python-dotenv undetected-chromedriver
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Common dependencies installed
)

:: Check if .env file exists
echo.
echo [6/7] Checking environment configuration...
if not exist ".env" (
    echo [WARNING] .env file not found
    echo Please create a .env file with the following variables:
    echo - ENROLLWARE_USERNAME
    echo - ENROLLWARE_PASSWORD
    echo - ATLAS_USERNAME
    echo - ATLAS_PASSWORD
    echo - SHOP_CPR_USERNAME
    echo - SHOP_CPR_PASSWORD
    echo - SHOP_CPR_SECURITY_ID
    echo.
    set /p continue="Continue anyway? (y/N): "
    if /i "!continue!" neq "y" (
        echo [INFO] Please create .env file and run again
        pause
        exit /b 1
    )
) else (
    echo [OK] Environment file found
)

:: Check if main.py exists
echo.
echo [7/7] Checking main application file...
if not exist "main.py" (
    echo [ERROR] main.py not found in current directory
    echo Current directory: %CD%
    dir *.py
    pause
    exit /b 1
)
echo [OK] main.py found

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

:: Run the application
echo.
echo ==========================================
echo    STARTING ENROLLWARE AUTOMATION
echo ==========================================
echo.
echo [INFO] Starting application...
echo [INFO] Log file: %logfile%
echo [INFO] Press Ctrl+C to stop the application
echo [INFO] Application output will be displayed below:
echo.
echo ==========================================

:: Run main.py and capture both stdout and stderr to log file while displaying on screen
echo [%date% %time%] Starting Enrollware Automation >> "%logfile%"
echo. >> "%logfile%"

:: Use a more compatible approach for logging
(
    echo Running: python main.py
    python main.py
) 2>&1 | (
    for /f "delims=" %%i in ('more') do (
        echo %%i
        echo [%date% %time%] %%i >> "%logfile%"
    )
)

set SCRIPT_EXIT_CODE=%errorlevel%

echo.
echo ==========================================
if %SCRIPT_EXIT_CODE% equ 0 (
    echo [SUCCESS] Application completed successfully
    echo [%date% %time%] Application completed successfully >> "%logfile%"
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

:: Show last few lines of log for quick reference
echo Last 10 lines of log:
echo ==========================================
if exist "%logfile%" (
    powershell "Get-Content '%logfile%' | Select-Object -Last 10"
) else (
    echo Log file not found
)
echo ==========================================
echo.

set /p view_log="View full log file? (y/N): "
if /i "!view_log!" equ "y" (
    if exist "%logfile%" (
        start notepad "%logfile%"
    )
)

pause

:: Deactivate virtual environment
call deactivate >nul 2>&1

exit /b %SCRIPT_EXIT_CODE%
