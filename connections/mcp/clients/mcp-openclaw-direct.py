#!/usr/bin/env python3
"""
OpenClaw Direct MCP Bridge
Talks to OpenClaw/Moltbot via CLI without Telegram
"""

import json
import sys
import subprocess
import os

def log(msg):
    print(f"[OPENCLAW-MCP] {msg}", file=sys.stderr)

VPS_IP = "77.42.66.40"
VPS_USER = "root"
SSH_KEY = os.path.expanduser("~/.ssh/ralf_hetzner")

def run_vps_command(cmd):
    """Run command on VPS via SSH"""
    try:
        result = subprocess.run(
            ["ssh", "-i", SSH_KEY, f"{VPS_USER}@{VPS_IP}", cmd],
            capture_output=True,
            text=True,
            timeout=120
        )
        return result
    except Exception as e:
        class FakeResult:
            stdout = ""
            stderr = str(e)
            returncode = 1
        return FakeResult()

def run_openclaw_agent(message, channel="telegram", to="7643203581", deliver=True):
    """Run OpenClaw agent and get response"""
    cmd_parts = [
        "openclaw", "agent",
        "--message", f'"{message}"',
        "--channel", channel,
        "--to", to,
        "--json"
    ]
    if deliver:
        cmd_parts.append("--deliver")

    cmd = " ".join(cmd_parts)

    try:
        result = run_vps_command(cmd)

        if result.returncode != 0:
            return f"Error: {result.stderr}"

        # Parse JSON response
        data = json.loads(result.stdout)
        if data.get("status") == "ok":
            payloads = data.get("result", {}).get("payloads", [])
            if payloads:
                return payloads[0].get("text", "No text response")
            return "No response payload"
        else:
            return f"Failed: {data}"

    except subprocess.TimeoutExpired:
        return "Timeout waiting for response"
    except Exception as e:
        return f"Error: {e}"

def get_openclaw_status():
    """Check if OpenClaw gateway is running"""
    try:
        result = run_vps_command("openclaw status --json")
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error: {e}"

def handle_tool_call(tool_name, args):
    if tool_name == "openclaw_ask":
        message = args.get("message", "")
        return {"content": [{"type": "text", "text": run_openclaw_agent(message)}]}

    elif tool_name == "openclaw_status":
        return {"content": [{"type": "text", "text": get_openclaw_status()}]}

    elif tool_name == "openclaw_check_ralf":
        # Ask OpenClaw to check RALF status
        return {"content": [{"type": "text", "text": run_openclaw_agent("Check the RALF system status. Are the planner and executor agents running? What's in the queue?")}]}

    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}

def main():
    log("OpenClaw Direct MCP Bridge starting...")

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
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "openclaw-direct", "version": "1.0.0"}
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
                                "name": "openclaw_ask",
                                "description": "Ask OpenClaw/Moltbot a question and get a response",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"message": {"type": "string"}},
                                    "required": ["message"]
                                }
                            },
                            {
                                "name": "openclaw_status",
                                "description": "Check OpenClaw gateway status",
                                "inputSchema": {"type": "object", "properties": {}}
                            },
                            {
                                "name": "openclaw_check_ralf",
                                "description": "Ask OpenClaw to check RALF system status",
                                "inputSchema": {"type": "object", "properties": {}}
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
                response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
                print(json.dumps(response))
                sys.stdout.flush()

        except json.JSONDecodeError:
            log(f"Invalid JSON: {line}")
        except Exception as e:
            log(f"Error: {e}")

if __name__ == "__main__":
    main()
