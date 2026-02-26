#!/bin/bash

# Define paths
SOURCE_DIR="/Users/peterbridger/Code/HDDSynth/2_prototype_mk2/software/"
DEST_DIR="/Volumes/CIRCUITPY/"

# Check if the Pico is actually mounted
if [ -d "$DEST_DIR" ]; then
    echo "🚀 Pico found! Syncing files..."
    
    # rsync flags:
    # -a: archive mode (preserves structures and symlinks)
    # -v: verbose (shows you what is happening)
    # --delete: removes files on the Pico that you deleted from your Mac
    # --exclude: ignores hidden Mac system files that can clutter the Pico
    rsync -av --delete \
        --exclude '.DS_Store' \
        --exclude '.git/' \
        "$SOURCE_DIR" "$DEST_DIR"
    
    echo "✅ Sync complete. You can now eject or wait for the Pico to reload."
else
    echo "❌ Error: CIRCUITPI not found at $DEST_DIR"
    echo "Make sure your Pico is plugged in and mounted."
    exit 1
fi
