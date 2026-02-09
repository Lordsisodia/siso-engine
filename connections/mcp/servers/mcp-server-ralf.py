#!/usr/bin/env python3
"""
RALF MCP Server for OpenClaw Integration
Runs on VPS to provide MCP tools for RALF task management
"""

import json
import sys
import subprocess
import os
from pathlib import Path

RALF_BASE = "/opt/ralf"
QUEUE_FILE = f"{RALF_BASE}/5-project-memory/blackbox5/.autonomous/agents/communications/queue.yaml"
EVENTS_FILE = f"{RALF_BASE}/5-project-memory/blackbox5/.autonomous/agents/communications/events.yaml"
VERIFY_FILE = f"{RALF_BASE}/5-project-memory/blackbox5/.autonomous/agents/communications/verify.yaml"


def log(msg):
    print(f"[RALF-MCP] {msg}", file=sys.stderr)


def read_yaml(path):
    """Read YAML file if it exists"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {path}: {e}"


def get_queue():
    """Get current task queue"""
    content = read_yaml(QUEUE_FILE)
    return content or "Queue is empty"


def get_events():
    """Get recent events"""
    content = read_yaml(EVENTS_FILE)
    return content or "No events"


def get_verify():
    """Get verification status"""
    content = read_yaml(VERIFY_FILE)
    return content or "No verifications"


def list_tasks():
    """List all tasks in queue"""
    return get_queue()


def get_task_status(task_id):
    """Get status of specific task"""
    queue = read_yaml(QUEUE_FILE) or ""
    for line in queue.split('\n'):
        if task_id in line:
            return line
    return f"Task {task_id} not found"


def run_ralf_command(cmd):
    """Execute a RALF command"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=RALF_BASE,
            timeout=30
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}


def handle_tool_call(tool_name, args):
    """Handle MCP tool calls"""
    if tool_name == "ralf_get_queue":
        return {"content": [{"type": "text", "text": get_queue()}]}

    elif tool_name == "ralf_get_events":
        return {"content": [{"type": "text", "text": get_events()}]}

    elif tool_name == "ralf_get_verify":
        return {"content": [{"type": "text", "text": get_verify()}]}

    elif tool_name == "ralf_list_tasks":
        return {"content": [{"type": "text", "text": list_tasks()}]}

    elif tool_name == "ralf_get_task_status":
        task_id = args.get("task_id", "")
        return {"content": [{"type": "text", "text": get_task_status(task_id)}]}

    elif tool_name == "ralf_run_command":
        cmd = args.get("command", "")
        result = run_ralf_command(cmd)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}


def main():
    log("RALF MCP Server starting...")

    # Send initialization response
    init_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "ralf-mcp-server",
                "version": "1.0.0"
            }
        }
    }
    print(json.dumps(init_response))
    sys.stdout.flush()

    # Send tools list
    tools_list = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "tools": [
                {
                    "name": "ralf_get_queue",
                    "description": "Get the current RALF task queue",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "ralf_get_events",
                    "description": "Get recent RALF events",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "ralf_get_verify",
                    "description": "Get verification status",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "ralf_list_tasks",
                    "description": "List all tasks in the queue",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "ralf_get_task_status",
                    "description": "Get status of a specific task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string", "description": "Task ID to check"}
                        },
                        "required": ["task_id"]
                    }
                },
                {
                    "name": "ralf_run_command",
                    "description": "Run a command in the RALF directory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Command to run"}
                        },
                        "required": ["command"]
                    }
                }
            ]
        }
    }
    print(json.dumps(tools_list))
    sys.stdout.flush()

    # Process incoming requests
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
            method = msg.get("method", "")
            msg_id = msg.get("id", 0)

            if method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": tools_list["result"]["tools"]
                    }
                }
                print(json.dumps(response))
                sys.stdout.flush()

            elif method == "tools/call":
                tool_name = msg.get("params", {}).get("name", "")
                args = msg.get("params", {}).get("arguments", {})
                result = handle_tool_call(tool_name, args)
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result
                }
                print(json.dumps(response))
                sys.stdout.flush()

        except json.JSONDecodeError:
            log(f"Invalid JSON: {line}")
        except Exception as e:
            log(f"Error: {e}")


if __name__ == "__main__":
    main()
