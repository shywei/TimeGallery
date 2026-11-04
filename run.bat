@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ====================================================
echo             Growing Up · 时光档案
echo ====================================================

call scripts\check_environment.bat
if %errorlevel% neq 0 (
    echo [ERROR] Environment check failed.
    pause
    exit /b 1
)

if not exist "frontend\dist\index.html" (
    echo [INFO] Frontend build not detected. Building frontend assets...
    call scripts\build.bat
)

echo [INFO] Launching Growing Up application...
call scripts\start.bat
