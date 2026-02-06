# RALF Monitor - Telegram Notification System

**Status:** Specification Complete - Ready for Implementation
**Purpose:** Real-time monitoring of BB5 agent sessions via Telegram

---

## Overview

RALF Monitor sends Telegram notifications when BB5 agents complete sessions. This provides:
- Real-time visibility into agent activity
- Token usage tracking
- Task completion monitoring
- Quick status checks without opening Claude Code

---

## Notification Triggers

### Primary Trigger: Stop Hook
Fires when agent session ends:
```json
{
  "session_id": "uuid",
  "transcript_path": "/path/to/transcript.jsonl",
  "duration_seconds": 3600
}
```

### Secondary Triggers (Future)
- Task claimed
- Task completed
- Error/exception occurred
- Token budget threshold reached

---

## Notification Format

### Standard Message Format

```
🤖 BB5 Agent Activity

📋 Agent: {agent_type}
📁 Project: {project_name}
🕐 Timestamp: {ISO8601}
📂 Run: {run_id}

📊 Session Stats:
• Duration: {X}h {Y}m
• Tokens Used: {N} ({percentage}% of budget)
• Task: {task_id} - {task_title}
• Status: {success|partial|blocked|error}

📈 Progress:
• Files Modified: {N}
• Tests Passed: {N}/{total}
• Documentation: {X}/5 files

🔗 Quick Links:
• Run Folder: {path}
• Task File: {path}
• Results: {path}
```

### Example Message

```
🤖 BB5 Agent Activity

📋 Agent: executor
📁 Project: blackbox5
🕐 Timestamp: 2026-02-06T14:32:00Z
📂 Run: run-20260206-143200

📊 Session Stats:
• Duration: 1h 12m
• Tokens Used: 45,230 (78% of budget)
• Task: TASK-ARCH-002 - Stop Hook Research
• Status: completed

📈 Progress:
• Files Modified: 8
• Tests Passed: N/A
• Documentation: 5/5 files

🔗 Quick Links:
• Run: ~/.blackbox5/5-project-memory/blackbox5/runs/run-20260206-143200
• Task: ~/.blackbox5/5-project-memory/blackbox5/tasks/active/TASK-ARCH-002/task.md
```

---

## Data Collection

### From Stop Hook Input
- `session_id`
- `transcript_path` (can parse for token usage)
- `duration_seconds`

### From Environment
- `BB5_PROJECT` (project name)
- `BB5_AGENT_TYPE` (agent type)
- `RALF_RUN_DIR` (run folder path)
- `CLAUDE_PROJECT_DIR` (project root)

### From Run Folder
- `metadata.yaml` (task_id, timestamps)
- `RESULTS.md` (status, completion %)
- File counts (documentation completeness)

### From Queue
- `queue.yaml` (task title, status)

### From Git
- Files modified count
- Commit hash (if committed)

---

## Implementation Options

### Option 1: Python Script (Recommended)

```python
#!/usr/bin/env python3
"""RALF Monitor - Telegram notifications for BB5 agents"""

import json
import sys
import os
import yaml
from datetime import datetime
from pathlib import Path

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = os.environ.get('RALF_TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('RALF_TELEGRAM_CHAT_ID')

def parse_stop_hook_input():
    """Parse JSON from stdin."""
    return json.load(sys.stdin)

def collect_session_data(input_data):
    """Collect all session data."""
    return {
        'agent_type': os.environ.get('BB5_AGENT_TYPE', 'unknown'),
        'project': os.environ.get('BB5_PROJECT', 'unknown'),
        'run_id': Path(os.environ.get('RALF_RUN_DIR', '')).name,
        'timestamp': datetime.now().isoformat(),
        'duration_seconds': input_data.get('duration_seconds', 0),
        'session_id': input_data.get('session_id', 'unknown'),
        # ... more fields
    }

def format_telegram_message(data):
    """Format data for Telegram."""
    # Format message as shown above
    pass

def send_telegram_message(message):
    """Send message via Telegram Bot API."""
    import requests

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }

    response = requests.post(url, json=payload)
    return response.ok

def main():
    # Parse input
    input_data = parse_stop_hook_input()

    # Collect data
    session_data = collect_session_data(input_data)

    # Format message
    message = format_telegram_message(session_data)

    # Send notification
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        send_telegram_message(message)

    # Always exit 0 (Stop hook shouldn't block)
    sys.exit(0)

if __name__ == '__main__':
    main()
```

### Option 2: Bash Script (Lightweight)

```bash
#!/bin/bash
# RALF Monitor - Lightweight Telegram notifications

# Read input from stdin
INPUT=$(cat)

# Extract fields using jq
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')
DURATION=$(echo "$INPUT" | jq -r '.duration_seconds')

# Get environment
AGENT_TYPE="${BB5_AGENT_TYPE:-unknown}"
PROJECT="${BB5_PROJECT:-unknown}"
RUN_ID=$(basename "${RALF_RUN_DIR:-unknown}")

# Format message
MESSAGE="🤖 BB5 Agent Activity

📋 Agent: $AGENT_TYPE
📁 Project: $PROJECT
📂 Run: $RUN_ID
⏱️ Duration: ${DURATION}s

# Send to Telegram
curl -s -X POST \
    "https://api.telegram.org/bot${RALF_TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${RALF_TELEGRAM_CHAT_ID}" \
    -d "text=${MESSAGE}" \
    -d "parse_mode=HTML"

exit 0
```

---

## Configuration

### Environment Variables

```bash
# Required
export RALF_TELEGRAM_BOT_TOKEN="your_bot_token"
export RALF_TELEGRAM_CHAT_ID="your_chat_id"

# Optional
export RALF_MONITOR_ENABLED="true"  # Enable/disable notifications
export RALF_MONITOR_MIN_DURATION="300"  # Only notify if session > 5 min
export RALF_MONITOR_INCLUDE_TOKENS="true"  # Include token usage
```

### Claude Code Settings

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/2-engine/.autonomous/hooks/active/ralf-monitor.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

---

## Telegram Bot Setup

### 1. Create Bot
1. Message @BotFather on Telegram
2. Create new bot: `/newbot`
3. Get bot token

### 2. Get Chat ID
1. Message @userinfobot
2. Get your chat ID

### 3. Test
```bash
curl -X POST \
    "https://api.telegram.org/bot<TOKEN>/sendMessage" \
    -d "chat_id=<CHAT_ID>" \
    -d "text=RALF Monitor test message"
```

---

## Future Enhancements

### v1.1
- [ ] Token usage from transcript parsing
- [ ] Error notification on failure
- [ ] Task completion celebration

### v1.2
- [ ] Daily/weekly summary reports
- [ ] Token budget alerts
- [ ] Project activity dashboard

### v2.0
- [ ] Interactive commands (/status, /tasks)
- [ ] Multi-channel support (different projects → different channels)
- [ ] Image attachments (screenshots, charts)

---

## Integration with Stop Hook

The RALF Monitor should be a **separate** Stop hook that runs alongside (or instead of) the validation hook:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/2-engine/.autonomous/hooks/active/ralf-monitor.py"
          },
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/2-engine/.autonomous/hooks/active/stop-cleanup.py"
          }
        ]
      }
    ]
  }
}
```

---

## Files

| File | Purpose |
|------|---------|
| `RALF_MONITOR_SPEC.md` | This specification |
| `ralf-monitor.py` | Implementation (Python) |
| `ralf-monitor.sh` | Implementation (Bash) |

---

*RALF Monitor - Keeping humans in the loop*
