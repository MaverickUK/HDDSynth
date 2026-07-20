#!/bin/bash

# Define paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/software/"
DEST_DIR="/Volumes/CIRCUITPY/"

# Check if the Pico is actually mounted
if [ -d "$DEST_DIR" ]; then
    echo "🚀 Pico found! Syncing files..."
    
    # rsync flags:
    # -a: archive mode (preserves structures and symlinks)
    # -v: verbose (shows you what is happening)
    # --delete: removes files on the Pico that you deleted from your Mac
    # --exclude: ignores hidden Mac system files that can clutter the Pico
    # rsync -av --delete \
    rsync -avm \
        --include='*.py' --include='*/' --exclude='*' \
        --exclude '.DS_Store' \
        --exclude '.git/' \
        "$SOURCE_DIR" "$DEST_DIR"
    
    echo "✅ Sync complete. You can now eject or wait for the Pico to reload."
else
    echo "❌ Error: CIRCUITPI not found at $DEST_DIR"
    echo "Make sure your Pico is plugged in and mounted."
    exit 1
fi
