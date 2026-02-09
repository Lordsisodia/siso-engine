#!/usr/bin/env python3
"""
Two-way MCP Bridge for Mac Mini OpenClaw
Polls Telegram messages and forwards them to Claude Code
"""

import asyncio
import json
import sys
import subprocess
import time
from datetime import datetime, timedelta

MACMINI_SSH = [
    "ssh", "-p", "14841",
    "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",
    "shaansisodia@4.tcp.eu.ngrok.io"
]

LAST_CHECKED = datetime.now() - timedelta(minutes=5)

def run_ssh_command(command):
    """Run command on Mac Mini via SSH"""
    full_cmd = MACMINI_SSH + [command]
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def get_recent_messages():
    """Get recent Telegram messages from OpenClaw logs"""
    # Check clawdbot logs for recent messages
    cmd = "export PATH=\"/opt/homebrew/bin:$PATH\" && clawdbot logs --limit 20 2>/dev/null | grep -i 'telegram\\|message\\|recv' | tail -10"
    return run_ssh_command(cmd)

def get_session_updates():
    """Get recent session activity"""
    cmd = "export PATH=\"/opt/homebrew/bin:$PATH\" && clawdbot sessions --limit 5 2>/dev/null"
    return run_ssh_command(cmd)

async def poll_for_updates():
    """Poll for new messages from OpenClaw"""
    messages = get_recent_messages()
    sessions = get_session_updates()

    updates = []
    if messages and "Error" not in messages:
        updates.append(f"📩 Recent Activity:\n{messages}")
    if sessions and "Error" not in sessions:
        updates.append(f"💬 Sessions:\n{sessions}")

    return "\n\n".join(updates) if updates else "No new updates"

async def main():
    while True:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line:
            break

        try:
            request = json.loads(line)
            method = request.get("method", "")
            params = request.get("params", {})

            if method == "tools/list":
                response = {
                    "tools": [
                        {
                            "name": "clawdbot_send_message",
                            "description": "Send message via Mac Mini OpenClaw",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "channel": {"type": "string", "enum": ["telegram", "whatsapp"]},
                                    "message": {"type": "string"}
                                },
                                "required": ["channel", "message"]
                            }
                        },
                        {
                            "name": "clawdbot_get_status",
                            "description": "Get Mac Mini OpenClaw status",
                            "inputSchema": {"type": "object"}
                        },
                        {
                            "name": "clawdbot_poll_updates",
                            "description": "Poll for recent messages and activity from OpenClaw",
                            "inputSchema": {"type": "object"}
                        },
                        {
                            "name": "clawdbot_conversation",
                            "description": "Send message and poll for response (two-way)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "wait_seconds": {"type": "integer", "default": 10}
                                },
                                "required": ["message"]
                            }
                        }
                    ]
                }
            elif method == "tools/call":
                tool = params.get("name", "")
                args = params.get("arguments", {})

                if tool == "clawdbot_send_message":
                    channel = args.get("channel", "telegram")
                    message = args.get("message", "")
                    target = "7643203581" if channel == "telegram" else "+447375099188"
                    cmd = f'export PATH="/opt/homebrew/bin:$PATH" && clawdbot message send --channel {channel} --target {target} --message "{message}"'
                    result = run_ssh_command(cmd)
                    response = {"content": [{"type": "text", "text": result}]}

                elif tool == "clawdbot_get_status":
                    cmd = 'export PATH="/opt/homebrew/bin:$PATH" && clawdbot status'
                    result = run_ssh_command(cmd)
                    response = {"content": [{"type": "text", "text": result}]}

                elif tool == "clawdbot_poll_updates":
                    result = await poll_for_updates()
                    response = {"content": [{"type": "text", "text": result}]}

                elif tool == "clawdbot_conversation":
                    # Send message
                    message = args.get("message", "")
                    wait = args.get("wait_seconds", 10)

                    send_cmd = f'export PATH="/opt/homebrew/bin:$PATH" && clawdbot message send --channel telegram --target 7643203581 --message "{message}"'
                    send_result = run_ssh_command(send_cmd)

                    # Wait and poll for response
                    await asyncio.sleep(wait)
                    updates = await poll_for_updates()

                    result = f"Sent: {send_result}\n\nResponse:\n{updates}"
                    response = {"content": [{"type": "text", "text": result}]}

                else:
                    response = {"error": f"Unknown tool: {tool}"}
            else:
                response = {"error": f"Unknown method: {method}"}

            response["jsonrpc"] = "2.0"
            response["id"] = request.get("id")
            print(json.dumps(response), flush=True)

        except Exception as e:
            error = {"jsonrpc": "2.0", "error": str(e), "id": request.get("id")}
            print(json.dumps(error), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
