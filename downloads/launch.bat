@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
python -m homunculus
if %ERRORLEVEL% neq 0 (
    echo.
    echo  [ERROR] Homunculus exited with an error.
    pause
)
