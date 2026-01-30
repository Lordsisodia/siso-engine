# Safety System

> Kill switch, content classification, and safe mode for Blackbox5

## Overview

The safety directory contains systems for controlling and monitoring AI behavior:
- **kill_switch/** - Emergency stop mechanism
- **classifier/** - Content safety classification
- **safe_mode/** - Safe execution mode (dry-run)

## Directory Structure

```
safety/
├── kill_switch/           # Emergency stop system
│   ├── kill_switch.py
│   ├── kill_switch_monitor.py
│   ├── keyboard_trigger.py
│   ├── cli_commands.py
│   └── tests/
├── classifier/            # Content classification
│   ├── classifier.py
│   ├── training_data.py
│   └── tests/
├── safe_mode/             # Safe execution mode
│   ├── safe_mode.py
│   ├── dry_run.py
│   └── tests/
├── tests/                 # Safety system tests
├── QUICK_REFERENCE.md
├── SAFETY-INTEGRATION-GUIDE.md
└── SAFETY-IMPLEMENTATION-COMPLETE.md
```

## Components

| Component | Purpose | Key File |
|-----------|---------|----------|
| Kill Switch | Emergency stop | `kill_switch/kill_switch.py` |
| Classifier | Content safety | `classifier/classifier.py` |
| Safe Mode | Dry-run execution | `safe_mode/safe_mode.py` |

## Usage

```python
# Kill switch
from core.safety.kill_switch import KillSwitch
kill_switch = KillSwitch()
kill_switch.activate()  # Emergency stop

# Safe mode
from core.safety.safe_mode import SafeMode
with SafeMode():
    # Operations run in dry-run mode
    pass
```

## For AI Agents

- Safety systems are critical - understand before modifying
- Kill switch can be triggered via keyboard or API
- Classifier checks content before execution
- Safe mode prevents destructive operations
- See `QUICK_REFERENCE.md` for quick commands
