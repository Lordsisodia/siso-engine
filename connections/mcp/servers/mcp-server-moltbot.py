#!/usr/bin/env python3
"""
Moltbot MCP Server - Connects to OpenClaw Gateway on VPS
Uses SSH to run openclaw commands on the VPS
"""

import json
import sys
import subprocess
import os

VPS_IP = "77.42.66.40"
VPS_USER = "root"
SSH_KEY = os.path.expanduser("~/.ssh/ralf_hetzner")


def log(msg):
    print(f"[MOLTBOT-MCP] {msg}", file=sys.stderr)


def run_vps_command(cmd):
    """Run a command on the VPS via SSH"""
    try:
        result = subprocess.run(
            ["ssh", "-i", SSH_KEY, f"{VPS_USER}@{VPS_IP}", cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}


def get_gateway_status():
    """Check if OpenClaw gateway is running"""
    result = run_vps_command("ps aux | grep openclaw | grep -v grep")
    return result.get("stdout", "Gateway not running")


def send_telegram_message(message):
    """Send a message via Telegram bot"""
    # Use openclaw CLI to send message
    cmd = f'openclaw message send --channel telegram --target 7643203581 --message "{message}" 2>&1'
    result = run_vps_command(cmd)
    return result.get("stdout", "No output") + result.get("stderr", "")


def get_ralf_status():
    """Get RALF status from the VPS"""
    cmd = "cat /opt/ralf/5-project-memory/blackbox5/.autonomous/agents/communications/queue.yaml 2>/dev/null | head -50"
    result = run_vps_command(cmd)
    return result.get("stdout", "Could not read queue")


def get_user_context():
    """Get user context from moltbot"""
    cmd = "cat /opt/moltbot/user-context.json 2>/dev/null"
    result = run_vps_command(cmd)
    return result.get("stdout", "No context found")


def handle_tool_call(tool_name, args):
    """Handle MCP tool calls"""
    if tool_name == "moltbot_get_status":
        return {"content": [{"type": "text", "text": get_gateway_status()}]}

    elif tool_name == "moltbot_send_message":
        message = args.get("message", "")
        return {"content": [{"type": "text", "text": send_telegram_message(message)}]}

    elif tool_name == "moltbot_get_ralf_status":
        return {"content": [{"type": "text", "text": get_ralf_status()}]}

    elif tool_name == "moltbot_get_user_context":
        return {"content": [{"type": "text", "text": get_user_context()}]}

    elif tool_name == "moltbot_run_command":
        cmd = args.get("command", "")
        result = run_vps_command(cmd)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}


def main():
    log("Moltbot MCP Server starting...")

    # Process incoming requests
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
            method = msg.get("method", "")
            msg_id = msg.get("id")

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "moltbot-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }
                print(json.dumps(response))
                sys.stdout.flush()

            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [
                            {
                                "name": "moltbot_get_status",
                                "description": "Get OpenClaw/Moltbot gateway status",
                                "inputSchema": {"type": "object", "properties": {}}
                            },
                            {
                                "name": "moltbot_send_message",
                                "description": "Send a message via Telegram",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string", "description": "Message to send"}
                                    },
                                    "required": ["message"]
                                }
                            },
                            {
                                "name": "moltbot_get_ralf_status",
                                "description": "Get RALF queue status",
                                "inputSchema": {"type": "object", "properties": {}}
                            },
                            {
                                "name": "moltbot_get_user_context",
                                "description": "Get user context from Moltbot",
                                "inputSchema": {"type": "object", "properties": {}}
                            },
                            {
                                "name": "moltbot_run_command",
                                "description": "Run a command on the VPS",
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
