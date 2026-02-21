#!/usr/bin/env bash
set -e

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║     Homunculus Setup v0.5.0           ║"
echo "  ║     Autonomous AI Agent               ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

# ── Step 0: Check Python ──
if ! command -v python3 &>/dev/null; then
    echo "  [ERROR] Python 3 not found."
    echo "  Install: https://python.org or 'brew install python3'"
    exit 1
fi
PYVER=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python ${PYVER} found."
echo ""

# ── Step 1: Download ──
DOWNLOAD_URL="https://sangjun0000.github.io/stellar-memory/downloads/homunculus-v0.5.0.zip"
TEMP_DIR=$(mktemp -d)
ZIP_FILE="${TEMP_DIR}/homunculus-v0.5.0.zip"

echo "  Downloading Homunculus..."
if command -v curl &>/dev/null; then
    curl -fsSL "$DOWNLOAD_URL" -o "$ZIP_FILE"
elif command -v wget &>/dev/null; then
    wget -q "$DOWNLOAD_URL" -O "$ZIP_FILE"
else
    echo "  [ERROR] curl or wget required."
    exit 1
fi
echo "  -> Downloaded."
echo ""

# ── Step 2: Extract ──
echo "  Extracting..."
unzip -qo "$ZIP_FILE" -d "$TEMP_DIR"
echo "  -> Extracted."
echo ""

# ── Step 3: Run installer ──
SOURCE_DIR="${TEMP_DIR}/homunculus-v0.5.0"
python3 "${SOURCE_DIR}/src/homunculus/installer.py" "${SOURCE_DIR}"

# ── Cleanup ──
rm -rf "$TEMP_DIR"

echo ""
echo "  Setup complete!"
