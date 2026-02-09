#!/usr/bin/env python3
"""
MCP Server for Mac Mini Clawdbot (OpenClaw)
Allows direct communication with OpenClaw from Claude Code
"""

import asyncio
import json
import sys
import subprocess

MACMINI_SSH = [
    "ssh", "-p", "14841",
    "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",
    "shaansisodia@4.tcp.eu.ngrok.io"
]

async def run_clawdbot_command(command):
    """Run a clawdbot command on Mac Mini"""
    full_command = MACMINI_SSH + ["export PATH=\"/opt/homebrew/bin:$PATH\" && " + command]
    process = await asyncio.create_subprocess_exec(
        *full_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode().strip() or stderr.decode().strip()

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
                            "description": "Send a message via Telegram/WhatsApp through Mac Mini OpenClaw",
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
                            "name": "clawdbot_run_agent",
                            "description": "Run an OpenClaw agent with a message",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "agent": {"type": "string", "default": "main"},
                                    "message": {"type": "string"}
                                },
                                "required": ["message"]
                            }
                        },
                        {
                            "name": "clawdbot_execute",
                            "description": "Execute a clawdbot CLI command",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "command": {"type": "string", "description": "Command to run (e.g., 'status', 'agents list')"}
                                },
                                "required": ["command"]
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
                    cmd = f'clawdbot message send --channel {channel} --target {target} --message "{message}"'
                    result = await run_clawdbot_command(cmd)
                    response = {"content": [{"type": "text", "text": result}]}

                elif tool == "clawdbot_get_status":
                    result = await run_clawdbot_command("clawdbot status")
                    response = {"content": [{"type": "text", "text": result}]}

                elif tool == "clawdbot_run_agent":
                    agent = args.get("agent", "main")
                    message = args.get("message", "")
                    cmd = f'clawdbot agent --agent {agent} --message "{message}" --local'
                    result = await run_clawdbot_command(cmd)
                    response = {"content": [{"type": "text", "text": result}]}

                elif tool == "clawdbot_execute":
                    command = args.get("command", "")
                    cmd = f"clawdbot {command}"
                    result = await run_clawdbot_command(cmd)
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
