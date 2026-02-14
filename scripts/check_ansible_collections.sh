#!/bin/bash
# Check if required Ansible collections are installed
# Run this on the machine where you execute ansible-playbook (controller)

set -e

echo "=== Ansible Collections Diagnostic ==="
echo ""

echo "1. Checking Ansible version..."
if command -v ansible &> /dev/null; then
    ansible --version | head -3
else
    echo "   ✗ Ansible not found!"
    exit 1
fi
echo ""

echo "2. Checking if community.general collection is installed..."
if ansible-galaxy collection list | grep -q "community.general"; then
    echo "   ✓ community.general is installed:"
    ansible-galaxy collection list | grep "community.general"
else
    echo "   ✗ community.general collection NOT found"
    echo "   This is required for homebrew_cask module!"
fi
echo ""

echo "3. Checking if community.docker collection is installed..."
if ansible-galaxy collection list | grep -q "community.docker"; then
    echo "   ✓ community.docker is installed:"
    ansible-galaxy collection list | grep "community.docker"
else
    echo "   ✗ community.docker collection NOT found"
fi
echo ""

echo "4. Listing all installed collections..."
echo "   (First 20 entries)"
ansible-galaxy collection list 2>/dev/null | head -20
echo ""

echo "=== Diagnostic Complete ==="
echo ""
echo "If collections are missing, install them with:"
echo "  ansible-galaxy collection install -r requirements.yml"
