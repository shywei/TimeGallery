@echo off
setlocal enabledelayedexpansion

echo ====================================================
echo   Growing Up - Checking Environment
echo ====================================================

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%USERPROFILE%\python-sdk\python3.13.2\python.exe" (
        set "PYTHON_EXE=%USERPROFILE%\python-sdk\python3.13.2\python.exe"
    ) else if exist "..\backend\.venv\Scripts\python.exe" (
        set "PYTHON_EXE=..\backend\.venv\Scripts\python.exe"
    ) else (
        echo [ERROR] Python not found in PATH or standard directory!
        exit /b 1
    )
) else (
    set "PYTHON_EXE=python"
)

echo [OK] Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version

REM Check Node
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js not found in PATH. Needed only for building frontend.
) else (
    echo [OK] Node.js found.
    node --version
)

echo ====================================================
echo   Environment check complete.
echo ====================================================
exit /b 0
