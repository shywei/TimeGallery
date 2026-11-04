@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\..\frontend"

echo Building frontend static assets...
call npm.cmd run build

if %errorlevel% equ 0 (
    echo [OK] Frontend built successfully. Dist output located at frontend\dist
) else (
    echo [ERROR] Frontend build failed.
    exit /b 1
)
