# TEST-01: File I/O with Hash Verification

## Task
Create a file with random content and verify its hash.

## Steps
1. Generate test ID: TEST-01-$(date +%s)
2. Create random content: "Moltbot test executed at $(date -Iseconds)"
3. Write to: /tmp/moltbot-test/${TEST_ID}.txt
4. Compute SHA256 hash of file
5. Read file back and verify content
6. Return JSON: {"test_id": "...", "hash": "...", "status": "success|failed"}

## Expected Output
```json
{
  "test_id": "TEST-01-1234567890",
  "hash": "sha256:abc123...",
  "status": "success"
}
```
