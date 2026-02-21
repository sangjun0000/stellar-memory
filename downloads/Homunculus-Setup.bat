@echo off
chcp 65001 >nul 2>&1
title Homunculus Setup
setlocal enabledelayedexpansion

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║     Homunculus Setup v1.0.0           ║
echo  ║     Autonomous AI Agent               ║
echo  ╚═══════════════════════════════════════╝
echo.

:: -- Step 1: Check Python --
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [!] Python not found.
    echo.
    echo  Homunculus requires Python 3.11+
    echo  Download: https://python.org
    echo  IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    echo  After installing Python, run this file again.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [1/6] Python %PYVER% found.

:: -- Step 2: Download --
set "DOWNLOAD_URL=https://sangjun0000.github.io/stellar-memory/downloads/homunculus-v1.0.0.zip"
set "TEMP_DIR=%TEMP%\homunculus-setup"
set "ZIP_FILE=%TEMP_DIR%\homunculus-v1.0.0.zip"
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

echo  [2/6] Downloading...
powershell -ExecutionPolicy Bypass -Command ^
  "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
  Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing } ^
  catch { exit 1 }"
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Download failed. Check your internet connection.
    pause
    exit /b 1
)

:: -- Step 3: Extract --
echo  [3/6] Extracting...
powershell -ExecutionPolicy Bypass -Command ^
  "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%TEMP_DIR%' -Force"

:: -- Step 4: Install (auto mode) --
set "SOURCE_DIR=%TEMP_DIR%\homunculus-v1.0.0"
if not exist "%SOURCE_DIR%\src\homunculus\installer.py" (
    echo  [ERROR] Invalid package. installer.py not found.
    pause
    exit /b 1
)
echo  [4/6] Installing...
python "%SOURCE_DIR%\src\homunculus\installer.py" "%SOURCE_DIR%" --auto
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Installation failed.
    pause
    exit /b 1
)

:: -- Step 5: Cleanup --
echo  [5/6] Cleaning up...
rmdir /s /q "%TEMP_DIR%" >nul 2>&1

:: -- Step 6: Auto-launch --
echo  [6/6] Launching Homunculus...
echo.
set "INSTALL_DIR=%USERPROFILE%\Homunculus"
if exist "%INSTALL_DIR%\launch.bat" (
    call "%INSTALL_DIR%\launch.bat"
) else (
    echo  Installation complete! Run Homunculus from your desktop shortcut.
    pause
)
