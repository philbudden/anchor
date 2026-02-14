#!/bin/bash
# Diagnostic script to check Docker Desktop installation status on remote Mac
# Run this on the Mac mini to diagnose why Docker wasn't installed

set -e

echo "=== Docker Desktop Installation Diagnostic ==="
echo ""

echo "1. Checking if Docker.app exists..."
if [ -d "/Applications/Docker.app" ]; then
    echo "   ✓ Docker.app found at /Applications/Docker.app"
    ls -la "/Applications/Docker.app" | head -3
else
    echo "   ✗ Docker.app NOT found at /Applications/Docker.app"
fi
echo ""

echo "2. Checking if Docker CLI is available..."
if command -v docker &> /dev/null; then
    echo "   ✓ Docker CLI found at: $(which docker)"
    docker --version 2>&1 || echo "   ✗ Docker CLI exists but failed to run"
else
    echo "   ✗ Docker CLI not found in PATH"
fi
echo ""

echo "3. Checking common Docker CLI locations..."
for path in /usr/local/bin/docker /opt/homebrew/bin/docker /Applications/Docker.app/Contents/Resources/bin/docker; do
    if [ -f "$path" ]; then
        echo "   ✓ Found: $path"
        $path --version 2>&1 || echo "     (failed to execute)"
    else
        echo "   ✗ Not found: $path"
    fi
done
echo ""

echo "4. Checking if Docker daemon is running..."
if docker info &> /dev/null; then
    echo "   ✓ Docker daemon is running"
    docker info | grep "Server Version" || true
else
    echo "   ✗ Docker daemon is NOT running (or CLI not accessible)"
fi
echo ""

echo "5. Checking Homebrew cask list..."
if command -v brew &> /dev/null; then
    echo "   Homebrew is available"
    echo "   Installed casks containing 'docker':"
    brew list --cask | grep -i docker || echo "   (none found)"
else
    echo "   ✗ Homebrew not found"
fi
echo ""

echo "6. Checking system architecture..."
echo "   $(uname -m) ($(uname -s))"
echo ""

echo "=== Diagnostic Complete ==="
echo ""
echo "Expected state after successful provisioning:"
echo "  - Docker.app should exist at /Applications/Docker.app"
echo "  - Docker CLI should be at /usr/local/bin/docker or /opt/homebrew/bin/docker"
echo "  - 'brew list --cask' should show 'docker'"
echo "  - Docker daemon may require manual first launch (macOS security)"
