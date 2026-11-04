@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

set "VENV_PYTHON=%CD%\backend\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    set "VENV_PYTHON=python"
)

"%VENV_PYTHON%" -c "from backend.app.services.backup_service import create_backup; res = create_backup(); print('Backup created:', res)"
