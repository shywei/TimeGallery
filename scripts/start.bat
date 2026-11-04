@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

set "VENV_PYTHON=%CD%\backend\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    if exist "%USERPROFILE%\python-sdk\python3.13.2\python.exe" (
        set "VENV_PYTHON=%USERPROFILE%\python-sdk\python3.13.2\python.exe"
    ) else (
        set "VENV_PYTHON=python"
    )
)

echo Starting Growing Up Server on http://127.0.0.1:8765 ...
"%VENV_PYTHON%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
