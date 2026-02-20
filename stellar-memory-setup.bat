@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   Stellar Memory - Setup
echo   AI Memory System Installer
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed.
    echo     Download from: https://www.python.org/downloads/
    echo     Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/3] Installing Stellar Memory...
pip install stellar-memory[mcp] --quiet
if %errorlevel% neq 0 (
    echo [!] Installation failed. Check your internet connection.
    pause
    exit /b 1
)

echo [2/3] Setting up MCP for AI IDE...
stellar-memory setup --yes
if %errorlevel% neq 0 (
    echo [!] MCP setup had issues, but Stellar Memory is installed.
    echo     You can run "stellar-memory setup" later.
)

echo [3/3] Done!
echo.
echo ============================================
echo   Installation complete!
echo.
echo   If you use Claude Desktop or Cursor,
echo   restart the app to activate AI memory.
echo.
echo   Try telling your AI: "Remember my name"
echo ============================================
pause
