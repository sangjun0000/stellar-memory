#!/usr/bin/env bash
set -e

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║     Homunculus Setup v0.5.0           ║"
echo "  ║     Autonomous AI Agent               ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

# -- Step 1: Check Python --
if ! command -v python3 &>/dev/null; then
    echo "  [!] Python 3 not found."
    echo ""
    echo "  Install Python 3.11+:"
    echo "    macOS:  brew install python3"
    echo "    Ubuntu: sudo apt install python3 python3-venv"
    echo "    Other:  https://python.org"
    echo ""
    echo "  Then run this script again."
    exit 1
fi
PYVER=$(python3 --version 2>&1 | awk '{print $2}')
echo "  [1/6] Python ${PYVER} found."

# -- Step 2: Download --
DOWNLOAD_URL="https://sangjun0000.github.io/stellar-memory/downloads/homunculus-v0.5.0.zip"
TEMP_DIR=$(mktemp -d)
ZIP_FILE="${TEMP_DIR}/homunculus-v0.5.0.zip"

echo "  [2/6] Downloading..."
if command -v curl &>/dev/null; then
    curl -fsSL "$DOWNLOAD_URL" -o "$ZIP_FILE"
elif command -v wget &>/dev/null; then
    wget -q "$DOWNLOAD_URL" -O "$ZIP_FILE"
else
    echo "  [ERROR] curl or wget required."
    exit 1
fi

# -- Step 3: Extract --
echo "  [3/6] Extracting..."
unzip -qo "$ZIP_FILE" -d "$TEMP_DIR"

# -- Step 4: Install (auto mode) --
SOURCE_DIR="${TEMP_DIR}/homunculus-v0.5.0"
echo "  [4/6] Installing..."
python3 "${SOURCE_DIR}/src/homunculus/installer.py" "${SOURCE_DIR}" --auto

# -- Step 5: Cleanup --
echo "  [5/6] Cleaning up..."
rm -rf "$TEMP_DIR"

# -- Step 6: Auto-launch --
echo "  [6/6] Launching Homunculus..."
echo ""
INSTALL_DIR="$HOME/Homunculus"
if [ -f "$INSTALL_DIR/launch.sh" ]; then
    exec "$INSTALL_DIR/launch.sh"
else
    echo "  Installation complete! Run: ~/Homunculus/launch.sh"
fi
