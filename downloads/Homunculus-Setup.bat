@echo off
chcp 65001 >nul 2>&1
title Homunculus Setup
setlocal enabledelayedexpansion

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║     Homunculus Setup v0.5.3           ║
echo  ║     Autonomous AI Agent               ║
echo  ╚═══════════════════════════════════════╝
echo.

:: -- Step 0: Check Python --
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Python not found.
    echo.
    echo  Please install Python 3.11+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during installation.
    goto :end
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Python %PYVER% found.
echo.

:: -- Step 1: Download --
set "DOWNLOAD_URL=https://sangjun0000.github.io/stellar-memory/downloads/homunculus-v0.5.3.zip"
set "TEMP_DIR=%TEMP%\homunculus-setup"
set "ZIP_FILE=%TEMP_DIR%\homunculus-v0.5.3.zip"

echo  Downloading Homunculus...
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

powershell -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing } catch { exit 1 }"
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Download failed. Check your internet connection.
    goto :end
)
echo  -^> Downloaded.
echo.

:: -- Step 2: Extract --
echo  Extracting...
powershell -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%TEMP_DIR%' -Force"
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Extraction failed.
    goto :end
)
echo  -^> Extracted.
echo.

:: -- Step 3: Run installer --
set "SOURCE_DIR=%TEMP_DIR%\homunculus-v0.5.3"
if not exist "%SOURCE_DIR%\src\homunculus\installer.py" (
    echo  [ERROR] Invalid package. installer.py not found.
    goto :end
)

python "%SOURCE_DIR%\src\homunculus\installer.py" "%SOURCE_DIR%"

:: -- Cleanup --
rmdir /s /q "%TEMP_DIR%" >nul 2>&1

:end
echo.
echo  Press any key to close...
pause >nul
