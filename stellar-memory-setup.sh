#!/usr/bin/env bash
set -e

echo "============================================"
echo "  Stellar Memory - Setup"
echo "  AI Memory System Installer"
echo "============================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is not installed."
    echo "    macOS: brew install python3"
    echo "    Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "    Other: https://www.python.org/downloads/"
    exit 1
fi

echo "[1/3] Installing Stellar Memory..."
pip3 install stellar-memory[mcp] --quiet

echo "[2/3] Setting up MCP for AI IDE..."
stellar-memory setup --yes || echo "[!] MCP setup had issues. Run 'stellar-memory setup' later."

echo "[3/3] Done!"
echo
echo "============================================"
echo "  Installation complete!"
echo
echo "  If you use Claude Desktop or Cursor,"
echo "  restart the app to activate AI memory."
echo
echo "  Try telling your AI: \"Remember my name\""
echo "============================================"
