#!/usr/bin/env python3
"""
OpenClaw SSH MCP Bridge - Two-Way Communication via SSH
Uses SSH to forward commands and receive responses
"""

import asyncio
import json
import sys
import subprocess
import threading
import queue
import time

VPS_IP = "77.42.66.40"
SSH_KEY = "/Users/shaansisodia/.ssh/ralf_hetzner"

# Message queue for async responses
message_queue = queue.Queue()

def run_vps_command(cmd, timeout=30):
    """Run command on VPS via SSH"""
    try:
        result = subprocess.run(
            ["ssh", "-i", SSH_KEY, f"root@{VPS_IP}", cmd],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip() + result.stderr.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def poll_telegram_messages():
    """Poll for Telegram messages via OpenClaw logs"""
    # Get recent messages from logs
    cmd = "cat /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log 2>/dev/null | grep -i 'telegram\\|message' | tail -20"
    return run_vps_command(cmd)

def send_telegram_message(message, target="7643203581"):
    """Send message via OpenClaw CLI"""
    cmd = f'openclaw message send --channel telegram --target {target} --message "{message}" 2>&1'
    return run_vps_command(cmd)

async def main():
    while True:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line:
            break

        try:
            request = json.loads(line)
            method = request.get("method", "")
            msg_id = request.get("id")

            if method == "tools/list":
                response = {
                    "tools": [
                        {
                            "name": "openclaw_send",
                            "description": "Send message via OpenClaw to Telegram",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "target": {"type": "string", "default": "7643203581"}
                                },
                                "required": ["message"]
                            }
                        },
                        {
                            "name": "openclaw_poll",
                            "description": "Poll for recent messages and activity",
                            "inputSchema": {"type": "object"}
                        },
                        {
                            "name": "openclaw_conversation",
                            "description": "Send message and poll for response (two-way)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "wait_seconds": {"type": "integer", "default": 15}
                                },
                                "required": ["message"]
                            }
                        },
                        {
                            "name": "openclaw_status",
                            "description": "Get OpenClaw status",
                            "inputSchema": {"type": "object"}
                        }
                    ]
                }

            elif method == "tools/call":
                tool = request.get("params", {}).get("name", "")
                args = request.get("params", {}).get("arguments", {})

                if tool == "openclaw_send":
                    message = args.get("message", "")
                    target = args.get("target", "7643203581")
                    result = send_telegram_message(message, target)
                    response = {"content": [{"type": "text", "text": result}]}

                elif tool == "openclaw_poll":
                    result = poll_telegram_messages()
                    response = {"content": [{"type": "text", "text": result or "No new activity"}]}

                elif tool == "openclaw_conversation":
                    message = args.get("message", "")
                    wait = args.get("wait_seconds", 15)

                    # Send message
                    send_result = send_telegram_message(message)

                    # Wait and poll
                    await asyncio.sleep(wait)
                    poll_result = poll_telegram_messages()

                    result = f"📤 Sent:\n{send_result}\n\n📥 Activity ({wait}s):\n{poll_result or 'No new messages'}"
                    response = {"content": [{"type": "text", "text": result}]}

                elif tool == "openclaw_status":
                    result = run_vps_command("ps aux | grep openclaw | grep -v grep")
                    status = "✅ Running" if "openclaw" in result else "❌ Not running"
                    response = {"content": [{"type": "text", "text": f"OpenClaw Status: {status}\n\n{result}"}]}

                else:
                    response = {"content": [{"type": "text", "text": f"Unknown tool: {tool}"}], "isError": True}

            else:
                response = {"error": f"Unknown method: {method}"}

            response["jsonrpc"] = "2.0"
            response["id"] = msg_id
            print(json.dumps(response), flush=True)

        except Exception as e:
            error = {"jsonrpc": "2.0", "error": str(e), "id": request.get("id")}
            print(json.dumps(error), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
