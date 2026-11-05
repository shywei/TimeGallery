@echo off
setlocal enabledelayedexpansion

set "PYTHONIOENCODING=utf-8"
set "PYTHON_EXE=%~dp0..\backend\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    if exist "%USERPROFILE%\python-sdk\python3.13.2\python.exe" (
        set "PYTHON_EXE=%USERPROFILE%\python-sdk\python3.13.2\python.exe"
    ) else (
        set "PYTHON_EXE=python"
    )
)

"%PYTHON_EXE%" "%~dp0package.py" %*
if %errorlevel% neq 0 (
    echo [ERROR] Packaging failed with exit code %errorlevel%.
    pause
    exit /b %errorlevel%
)
