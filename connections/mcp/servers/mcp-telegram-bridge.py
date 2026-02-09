#!/usr/bin/env python3
"""
Telegram Two-Way MCP Bridge
Sends messages and polls for responses
"""

import json
import sys
import os
import time
import requests

BOT_TOKEN = "8581639813:AAFA13wDTKEX2x6J-lVfpq9QHnsGRnB1EZo"
CHAT_ID = "7643203581"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def log(msg):
    print(f"[TELEGRAM-MCP] {msg}", file=sys.stderr)

def send_message(text):
    """Send a message via Telegram"""
    try:
        resp = requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text},
            timeout=10
        )
        data = resp.json()
        if data.get("ok"):
            return f"Message sent (ID: {data['result']['message_id']})"
        return f"Failed: {data}"
    except Exception as e:
        return f"Error: {e}"

def get_updates(offset=None, timeout=30):
    """Get updates with long polling"""
    try:
        params = {"timeout": timeout, "limit": 10}
        if offset:
            params["offset"] = offset
        resp = requests.get(
            f"{BASE_URL}/getUpdates",
            params=params,
            timeout=timeout + 10
        )
        data = resp.json()
        if data.get("ok"):
            return data["result"]
        return []
    except Exception as e:
        log(f"Error getting updates: {e}")
        return []

def send_and_wait(text, wait_seconds=60):
    """Send message and wait for a response"""
    # First send the message
    send_result = send_message(text)
    log(f"Sent: {send_result}")

    # Get current offset
    updates = get_updates(timeout=5)
    if updates:
        offset = updates[-1]["update_id"] + 1
    else:
        offset = None

    # Wait for response
    start_time = time.time()
    while time.time() - start_time < wait_seconds:
        updates = get_updates(offset=offset, timeout=10)
        for update in updates:
            if "message" in update:
                msg = update["message"]
                if str(msg.get("chat", {}).get("id")) == CHAT_ID:
                    if msg.get("from", {}).get("is_bot"):
                        continue  # Skip bot messages
                    return f"Response from {msg.get('from', {}).get('first_name')}: {msg.get('text', '[no text]')}"
                offset = update["update_id"] + 1
        time.sleep(1)

    return "No response received within timeout"

def handle_tool_call(tool_name, args):
    if tool_name == "telegram_send":
        message = args.get("message", "")
        return {"content": [{"type": "text", "text": send_message(message)}]}

    elif tool_name == "telegram_send_and_wait":
        message = args.get("message", "")
        timeout = args.get("timeout", 60)
        return {"content": [{"type": "text", "text": send_and_wait(message, timeout)}]}

    elif tool_name == "telegram_get_updates":
        updates = get_updates()
        texts = []
        for u in updates:
            if "message" in u:
                m = u["message"]
                texts.append(f"{m.get('from', {}).get('first_name')}: {m.get('text', '[no text]')}")
        return {"content": [{"type": "text", "text": "\n".join(texts) or "No new messages"}]}

    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}

def main():
    log("Telegram MCP Bridge starting...")

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
                        "serverInfo": {"name": "telegram-bridge", "version": "1.0.0"}
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
                                "name": "telegram_send",
                                "description": "Send a message via Telegram",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"message": {"type": "string"}},
                                    "required": ["message"]
                                }
                            },
                            {
                                "name": "telegram_send_and_wait",
                                "description": "Send message and wait for response",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "timeout": {"type": "number", "description": "Seconds to wait"}
                                    },
                                    "required": ["message"]
                                }
                            },
                            {
                                "name": "telegram_get_updates",
                                "description": "Get recent messages",
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
