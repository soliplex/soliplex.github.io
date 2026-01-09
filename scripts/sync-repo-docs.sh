#!/bin/bash
set -e

# ============================================================================
# Sync Repository Documentation Script
# ============================================================================
# This script fetches documentation from a remote Git repository and copies
# it to the local documentation site using sparse checkout for efficiency.
#
# Usage:
#   ./sync-repo-docs.sh <REPO> <TARGET_DIR> <SOURCE_PATH>
#
# Arguments:
#   REPO        - GitHub repository (e.g., "soliplex/soliplex")
#   TARGET_DIR  - Local destination directory (e.g., "docs/soliplex")
#   SOURCE_PATH - Path in source repo (e.g., "docs" or "README.md")
#
# Example:
#   ./sync-repo-docs.sh soliplex/soliplex docs/soliplex docs
# ============================================================================

# Check arguments
if [ $# -ne 3 ]; then
    echo "Error: Invalid number of arguments"
    echo "Usage: $0 <REPO> <TARGET_DIR> <SOURCE_PATH>"
    echo ""
    echo "Example: $0 soliplex/soliplex docs/soliplex docs"
    exit 1
fi

REPO=$1           # e.g., "soliplex/soliplex"
TARGET_DIR=$2     # e.g., "docs/soliplex"
SOURCE_PATH=$3    # e.g., "docs" or "README.md"

# Save original working directory
ORIGINAL_DIR=$(pwd)

echo "============================================================"
echo "Syncing documentation from $REPO"
echo "============================================================"
echo "Repository:   $REPO"
echo "Source path:  $SOURCE_PATH"
echo "Target dir:   $TARGET_DIR"
echo "Work dir:     $ORIGINAL_DIR"
echo "------------------------------------------------------------"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Temp dir:     $TEMP_DIR"

# Trap to ensure cleanup on exit
cleanup() {
    echo "Cleaning up temporary directory..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

cd "$TEMP_DIR"

# Clone only the docs (sparse checkout for efficiency)
echo ""
echo "Cloning repository (sparse checkout)..."
git clone --depth 1 --filter=blob:none --sparse \
  "https://github.com/$REPO.git" repo

if [ $? -ne 0 ]; then
    echo "Error: Failed to clone repository $REPO"
    exit 1
fi

cd repo

# Set up sparse checkout for the specific path
echo ""
echo "Configuring sparse checkout for: $SOURCE_PATH"
git sparse-checkout set "$SOURCE_PATH"

if [ $? -ne 0 ]; then
    echo "Error: Failed to configure sparse checkout for $SOURCE_PATH"
    exit 1
fi

# Verify the source path exists
cd "$ORIGINAL_DIR"
if [ ! -e "$TEMP_DIR/repo/$SOURCE_PATH" ]; then
    echo "Error: Source path '$SOURCE_PATH' not found in repository"
    echo "Available paths in repo:"
    ls -la "$TEMP_DIR/repo/" || echo "Cannot list directory"
    exit 1
fi

# Copy docs to target
echo ""
echo "Copying documentation to target directory..."
echo "Current dir: $(pwd)"

# Remove existing target directory
if [ -d "$TARGET_DIR" ]; then
    echo "Removing existing directory: $TARGET_DIR"
    rm -rf "$TARGET_DIR"
fi

# Create parent directory if needed
mkdir -p "$(dirname "$TARGET_DIR")"

# Copy based on whether source is a file or directory
if [ -d "$TEMP_DIR/repo/$SOURCE_PATH" ]; then
    echo "Copying directory: $SOURCE_PATH -> $TARGET_DIR"
    cp -r "$TEMP_DIR/repo/$SOURCE_PATH" "$TARGET_DIR"

    # Count files copied
    FILE_COUNT=$(find "$TARGET_DIR" -type f | wc -l)
    echo "Copied $FILE_COUNT files"

elif [ -f "$TEMP_DIR/repo/$SOURCE_PATH" ]; then
    echo "Copying file: $SOURCE_PATH -> $TARGET_DIR/"
    mkdir -p "$TARGET_DIR"
    cp "$TEMP_DIR/repo/$SOURCE_PATH" "$TARGET_DIR/"
    echo "Copied 1 file"
else
    echo "Error: Source path is neither a file nor directory"
    exit 1
fi

echo ""
echo "✓ Successfully synced $REPO to $TARGET_DIR"
echo "============================================================"
