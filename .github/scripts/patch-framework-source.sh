#!/bin/bash
# Patch pyproject.toml to use git source instead of local path for CI
set -e

if [ -f "pyproject.toml" ]; then
    # Replace local path with git+https source (works on both Linux and macOS)
    if sed --version 2>&1 | grep -q GNU; then
        # GNU sed (Linux)
        sed -i 's|arclith = { path = "../framework", editable = true }|arclith = { git = "https://github.com/karned-rekipe/framework.git", branch = "feat/config-dir-adapter-registry-export-cli" }|' pyproject.toml
    else
        # BSD sed (macOS)
        sed -i '' 's|arclith = { path = "../framework", editable = true }|arclith = { git = "https://github.com/karned-rekipe/framework.git", branch = "feat/config-dir-adapter-registry-export-cli" }|' pyproject.toml
    fi
    echo "✓ pyproject.toml patched for CI"
    grep "arclith" pyproject.toml
fi


