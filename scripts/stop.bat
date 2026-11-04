@echo off
setlocal enabledelayedexpansion

echo Finding process listening on port 8765...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8765" ^| findstr "LISTENING"') do (
    set "PID=%%a"
    echo Stopping Growing Up server PID !PID!...
    taskkill /F /PID !PID! >nul 2>&1
    echo Server stopped successfully.
    goto :done
)

echo No active Growing Up server found on port 8765.

:done
exit /b 0
