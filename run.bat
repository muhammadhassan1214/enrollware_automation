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
echo [%date% %time%] Log file: %logfile% >> "%logfile%"
echo [%date% %time%] Current directory: %CD% >> "%logfile%"
echo [%date% %time%] Python version: >> "%logfile%"
python --version >> "%logfile%" 2>&1
echo. >> "%logfile%"
echo [%date% %time%] ==========================================  >> "%logfile%"
echo [%date% %time%] APPLICATION OUTPUT: >> "%logfile%"
echo [%date% %time%] ==========================================  >> "%logfile%"

:: Run Python script with proper output capture and real-time display
echo Running: python main.py
echo.

:: Use PowerShell to handle real-time output and logging
powershell -Command "& {
    $process = Start-Process -FilePath 'python' -ArgumentList 'main.py' -NoNewWindow -PassThru -RedirectStandardOutput 'temp_stdout.txt' -RedirectStandardError 'temp_stderr.txt'

    # Monitor output files and display/log in real-time
    $stdout_pos = 0
    $stderr_pos = 0

    while (-not $process.HasExited) {
        # Check stdout
        if (Test-Path 'temp_stdout.txt') {
            $content = Get-Content 'temp_stdout.txt' -Raw
            if ($content.Length -gt $stdout_pos) {
                $new_content = $content.Substring($stdout_pos)
                Write-Host $new_content -NoNewline
                Add-Content '%logfile%' \"[$(Get-Date)] STDOUT: $new_content\"
                $stdout_pos = $content.Length
            }
        }

        # Check stderr
        if (Test-Path 'temp_stderr.txt') {
            $content = Get-Content 'temp_stderr.txt' -Raw
            if ($content.Length -gt $stderr_pos) {
                $new_content = $content.Substring($stderr_pos)
                Write-Host $new_content -NoNewline -ForegroundColor Red
                Add-Content '%logfile%' \"[$(Get-Date)] STDERR: $new_content\"
                $stderr_pos = $content.Length
            }
        }

        Start-Sleep -Milliseconds 100
    }

    # Get final output
    if (Test-Path 'temp_stdout.txt') {
        $content = Get-Content 'temp_stdout.txt' -Raw
        if ($content.Length -gt $stdout_pos) {
            $new_content = $content.Substring($stdout_pos)
            Write-Host $new_content -NoNewline
            Add-Content '%logfile%' \"[$(Get-Date)] STDOUT: $new_content\"
        }
    }

    if (Test-Path 'temp_stderr.txt') {
        $content = Get-Content 'temp_stderr.txt' -Raw
        if ($content.Length -gt $stderr_pos) {
            $new_content = $content.Substring($stderr_pos)
            Write-Host $new_content -NoNewline -ForegroundColor Red
            Add-Content '%logfile%' \"[$(Get-Date)] STDERR: $new_content\"
        }
    }

    exit $process.ExitCode
}"

set SCRIPT_EXIT_CODE=%errorlevel%

:: Clean up temporary files
if exist "temp_stdout.txt" del "temp_stdout.txt" >nul 2>&1
if exist "temp_stderr.txt" del "temp_stderr.txt" >nul 2>&1

:: Add completion status to log
echo. >> "%logfile%"
echo [%date% %time%] ==========================================  >> "%logfile%"

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

:: Show log file size and last modification
if exist "%logfile%" (
    for %%F in ("%logfile%") do (
        echo Log file size: %%~zF bytes
        echo Last modified: %%~tF
    )
    echo.
)

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
