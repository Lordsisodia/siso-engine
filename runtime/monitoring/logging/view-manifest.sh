#!/bin/bash
# view-manifest.sh - View operation manifests for Blackbox 5
# Usage: ./view-manifest.sh [manifest_id]
#   If no ID provided, lists recent manifests

set -e

# Configuration
MANIFEST_DIR="blackbox5/scratch/manifests"

# Parse arguments
MANIFEST_ID=""
SHOW_ALL=false
LIST_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all|-a)
            SHOW_ALL=true
            shift
            ;;
        --list|-l)
            LIST_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [manifest_id] [options]"
            echo ""
            echo "Arguments:"
            echo "  manifest_id  ID of the manifest to view (optional)"
            echo ""
            echo "Options:"
            echo "  --all, -a     List all manifests (not just recent)"
            echo "  --list, -l    Only list manifests, don't display content"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # List recent manifests"
            echo "  $0 --all              # List all manifests"
            echo "  $0 abc123-def456      # View specific manifest"
            echo "  $0 --list abc123      # List only, don't show content"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Use -h for help"
            exit 1
            ;;
        *)
            MANIFEST_ID="$1"
            shift
            ;;
    esac
done

# Check if manifest directory exists
if [ ! -d "$MANIFEST_DIR" ]; then
    echo "Manifest directory not found: $MANIFEST_DIR"
    echo ""
    echo "This directory will be created when the system runs operations."
    echo "Manifests track the execution of multi-agent operations."
    exit 1
fi

# Check if any manifests exist
if [ -z "$(ls -A $MANIFEST_DIR 2>/dev/null)" ]; then
    echo "No manifests found in: $MANIFEST_DIR"
    echo ""
    echo "Manifests are created during multi-agent operations."
    exit 1
fi

# Function to list manifests
list_manifests() {
    local count=$1

    echo "=============================================="
    echo "Blackbox 5 Operation Manifests"
    echo "=============================================="
    echo "Directory: $MANIFEST_DIR"
    echo "Count: $(ls -1 "$MANIFEST_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ') manifests"
    echo "=============================================="
    echo ""

    # List manifests sorted by date (newest first)
    ls -t "$MANIFEST_DIR"/*.md 2>/dev/null | head -n "$count" | while read -r manifest_file; do
        local filename=$(basename "$manifest_file" .md)
        local filepath="$manifest_file"

        # Extract metadata from manifest
        local type=$(grep -E "^## Metadata" -A 10 "$filepath" | grep "Type:" | sed 's/.*Type: //' | xargs || echo "unknown")
        local status=$(grep -E "^## Metadata" -A 10 "$filepath" | grep "Status:" | sed 's/.*Status: //' | xargs || echo "unknown")
        local started=$(grep -E "^## Metadata" -A 10 "$filepath" | grep "Started:" | sed 's/.*Started: //' | xargs || echo "unknown")

        # Format display
        local status_symbol="?"
        case "$status" in
            "completed"|"COMPLETED")
                status_symbol="✓"
                ;;
            "failed"|"FAILED")
                status_symbol="✗"
                ;;
            "in_progress"|"IN_PROGRESS")
                status_symbol="⟳"
                ;;
            "pending"|"PENDING")
                status_symbol="○"
                ;;
        esac

        printf "%s %-12s %-20s %s\n" "$status_symbol" "$status" "$type" "$filename"
        printf "    Started: %s\n" "$started"
        echo ""
    done
}

# Function to display a manifest
display_manifest() {
    local manifest_file="$1"

    if [ ! -f "$manifest_file" ]; then
        echo "Error: Manifest not found: $manifest_file"
        exit 1
    fi

    echo "=============================================="
    echo "Operation Manifest"
    echo "=============================================="
    echo "File: $manifest_file"
    echo "=============================================="
    echo ""

    # Display the manifest content
    cat "$manifest_file"

    echo ""
    echo "=============================================="
    echo ""
    echo "Quick Actions:"
    echo "  View logs: ./view-logs.sh"
    echo "  Check status: ./agent-status.sh"
    echo "=============================================="
}

# Main logic
if [ -z "$MANIFEST_ID" ]; then
    # No manifest ID provided, list recent manifests
    if [ "$SHOW_ALL" = true ]; then
        list_manifests 9999
    else
        list_manifests 10
    fi
elif [ "$LIST_ONLY" = true ]; then
    # List only mode
    list_manifests 9999 | grep -E "^(\[|○|⟳|✓|✗|===|Directory|Count|Blackbox)" || list_manifests 10
else
    # Display specific manifest
    MANIFEST_FILE="$MANIFEST_DIR/$MANIFEST_ID.md"

    if [ ! -f "$MANIFEST_FILE" ]; then
        echo "Manifest not found: $MANIFEST_ID"
        echo ""
        echo "Available manifests:"
        list_manifests 10
        exit 1
    fi

    display_manifest "$MANIFEST_FILE"
fi
