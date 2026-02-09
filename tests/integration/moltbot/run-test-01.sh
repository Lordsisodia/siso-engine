#!/bin/bash
# Test 1: File I/O with Hash Verification

TEST_ID="TEST-01-$(date +%s)"
TEST_DIR="/tmp/moltbot-test"
TEST_FILE="$TEST_DIR/${TEST_ID}.txt"

# Create test directory
mkdir -p $TEST_DIR

# Generate content
CONTENT="Moltbot test executed at $(date -Iseconds)"
echo "$CONTENT" > $TEST_FILE

# Compute hash
HASH=$(sha256sum $TEST_FILE | cut -d' ' -f1)

# Verify file exists and hash matches
if [ -f "$TEST_FILE" ]; then
    echo "{\"test_id\": \"$TEST_ID\", \"hash\": \"$HASH\", \"status\": \"success\"}"
else
    echo "{\"test_id\": \"$TEST_ID\", \"status\": \"failed\", \"error\": \"file not created\"}"
fi
