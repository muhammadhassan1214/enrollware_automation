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
echo [1/6] Checking Python installation...
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
echo [2/6] Checking pip installation...
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
echo [3/6] Checking virtual environment...
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
echo [4/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

:: Check and install requirements
echo.
echo [5/6] Checking dependencies...
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
echo [6/6] Checking environment configuration...
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
if not exist "main.py" (
    echo [ERROR] main.py not found in current directory
    pause
    exit /b 1
)

:: Create logs directory if it doesn't exist
if not exist "logs\" (
    mkdir logs
    echo [INFO] Created logs directory
)

:: Run the application
echo.
echo ==========================================
echo    STARTING ENROLLWARE AUTOMATION
echo ==========================================
echo.
echo [INFO] Starting application...
echo [INFO] Logs will be saved in the logs directory
echo [INFO] Press Ctrl+C to stop the application
echo.

:: Set log file with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

:: Run main.py with logging
python main.py 2>&1 | tee logs\run_%timestamp%.log
set SCRIPT_EXIT_CODE=%errorlevel%

echo.
echo ==========================================
if %SCRIPT_EXIT_CODE% equ 0 (
    echo [SUCCESS] Application completed successfully
    color 0A
) else (
    echo [ERROR] Application exited with error code: %SCRIPT_EXIT_CODE%
    color 0C
)
echo ==========================================
echo.
echo Log file: logs\run_%timestamp%.log
echo.
pause

:: Deactivate virtual environment
deactivate

exit /b %SCRIPT_EXIT_CODE%

