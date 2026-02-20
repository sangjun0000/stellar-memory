#!/bin/bash
set -e

MSG="${1:-Update landing page}"
SRC="landing/index.html"
TMP="/tmp/_stellar_deploy.html"

echo "Deploying landing page..."

# Copy current file to temp
cp "$SRC" "$TMP"

# Stash any in-progress changes
git stash -q 2>/dev/null || true

# Switch to gh-pages branch
git checkout gh-pages -q

# Update both root and landing index.html
cp "$TMP" index.html
cp "$TMP" landing/index.html

# Commit & push
git add index.html landing/index.html
git commit -m "$MSG" -q
git push origin gh-pages -q

# Return to main branch
git checkout main -q
git stash pop -q 2>/dev/null || true

# Clean up
rm -f "$TMP"

echo "Deployed to https://stellar-memory.com"
