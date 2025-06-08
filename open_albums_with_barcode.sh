#!/bin/bash

# Script to open processed album directories in separate Finder windows
# and prompt for barcode scanning for each album using the local database

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUMMARY_FILE="../processed_albums_summary.txt"
PYTHON_SCRIPT="$SCRIPT_DIR/barcode_lookup.py"

if [ ! -f "$SUMMARY_FILE" ]; then
    echo "Error: $SUMMARY_FILE not found!"
    exit 1
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: $PYTHON_SCRIPT not found!"
    exit 1
fi

echo "Opening processed album directories in Finder and scanning barcodes..."

# Use grep to find lines with "Local path:" and extract the path
grep "Local path:" "$SUMMARY_FILE" | sed 's/  Local path: //' | while read -r album_path; do
    if [ -d "$album_path" ]; then
        # Extract artist and album from path
        album_name=$(basename "$album_path")
        artist_name=$(basename "$(dirname "$album_path")")
        
        echo "========================================="
        echo "Opening: $artist_name - $album_name"
        echo "Path: $album_path"
        open "$album_path"
        
        # Prompt for barcode
        echo "Scan barcode for $artist_name - $album_name (or press Enter to skip):"
        read barcode
        
        if [ ! -z "$barcode" ]; then
            echo "Looking up barcode: $barcode"
            python3 "$PYTHON_SCRIPT" "$barcode"
        fi
    else
        echo "Directory not found: $album_path"
    fi
done

echo "Done opening album directories and scanning barcodes."
