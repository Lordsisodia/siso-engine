#!/usr/bin/env python3
"""
OpenClaw WebSocket MCP Bridge - True Two-Way Communication
Connects Claude Code directly to OpenClaw gateway via WebSocket
"""

import asyncio
import json
import sys
import websockets
import threading
import queue
import time

# OpenClaw VPS config
VPS_IP = "77.42.66.40"
GATEWAY_PORT = 18789
GATEWAY_TOKEN = "ralf-local-token-12345"  # From openclaw.json

# Message queue for responses
response_queue = queue.Queue()

async def connect_to_gateway():
    """Connect to OpenClaw WebSocket gateway"""
    uri = f"ws://{VPS_IP}:{GATEWAY_PORT}?token={GATEWAY_TOKEN}"
    try:
        websocket = await websockets.connect(uri)
        print(f"[OpenClaw Bridge] Connected to {uri}", file=sys.stderr)
        return websocket
    except Exception as e:
        print(f"[OpenClaw Bridge] Connection failed: {e}", file=sys.stderr)
        return None

async def receive_messages(websocket):
    """Continuously receive messages from OpenClaw"""
    while True:
        try:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"[OpenClaw Bridge] Received: {data}", file=sys.stderr)
            response_queue.put(data)
        except websockets.exceptions.ConnectionClosed:
            print("[OpenClaw Bridge] Connection closed", file=sys.stderr)
            break
        except Exception as e:
            print(f"[OpenClaw Bridge] Error: {e}", file=sys.stderr)
            break

async def send_message(websocket, message_text, target="7643203581"):
    """Send message via OpenClaw"""
    payload = {
        "type": "message.send",
        "channel": "telegram",
        "target": target,
        "message": message_text
    }
    await websocket.send(json.dumps(payload))
    return {"status": "sent", "message": message_text}

async def main():
    # Connect to gateway
    websocket = await connect_to_gateway()
    if not websocket:
        print("[OpenClaw Bridge] Failed to connect, running in limited mode", file=sys.stderr)

    # Start receiver in background
    if websocket:
        receiver_task = asyncio.create_task(receive_messages(websocket))

    # Process MCP requests
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
                            "description": "Send message to OpenClaw (Telegram/WhatsApp)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "channel": {"type": "string", "default": "telegram"}
                                },
                                "required": ["message"]
                            }
                        },
                        {
                            "name": "openclaw_receive",
                            "description": "Receive messages from OpenClaw (poll for responses)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "timeout": {"type": "integer", "default": 10}
                                }
                            }
                        },
                        {
                            "name": "openclaw_conversation",
                            "description": "Send message and wait for response (two-way)",
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
                            "description": "Get OpenClaw connection status",
                            "inputSchema": {"type": "object"}
                        }
                    ]
                }

            elif method == "tools/call":
                tool = request.get("params", {}).get("name", "")
                args = request.get("params", {}).get("arguments", {})

                if tool == "openclaw_send":
                    if websocket:
                        result = await send_message(websocket, args.get("message", ""))
                        response = {"content": [{"type": "text", "text": json.dumps(result)}]}
                    else:
                        response = {"content": [{"type": "text", "text": "Not connected to OpenClaw"}], "isError": True}

                elif tool == "openclaw_receive":
                    # Poll for messages from queue
                    timeout = args.get("timeout", 10)
                    messages = []
                    try:
                        while True:
                            msg = response_queue.get(timeout=timeout)
                            messages.append(msg)
                    except queue.Empty:
                        pass

                    if messages:
                        response = {"content": [{"type": "text", "text": json.dumps(messages, indent=2)}]}
                    else:
                        response = {"content": [{"type": "text", "text": "No new messages"}]}

                elif tool == "openclaw_conversation":
                    # Send and wait for response
                    message = args.get("message", "")
                    wait = args.get("wait_seconds", 15)

                    if websocket:
                        await send_message(websocket, message)

                        # Wait for response
                        await asyncio.sleep(wait)

                        # Collect messages
                        messages = []
                        try:
                            while True:
                                msg = response_queue.get_nowait()
                                messages.append(msg)
                        except queue.Empty:
                            pass

                        result = f"Sent: {message}\n\nReceived:\n{json.dumps(messages, indent=2) if messages else 'No response yet'}"
                        response = {"content": [{"type": "text", "text": result}]}
                    else:
                        response = {"content": [{"type": "text", "text": "Not connected to OpenClaw"}], "isError": True}

                elif tool == "openclaw_status":
                    status = "Connected" if websocket else "Disconnected"
                    response = {"content": [{"type": "text", "text": f"OpenClaw WebSocket: {status}"}]}

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

    if websocket:
        await websocket.close()

if __name__ == "__main__":
    asyncio.run(main())
