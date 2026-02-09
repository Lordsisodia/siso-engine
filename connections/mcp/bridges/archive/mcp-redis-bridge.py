#!/usr/bin/env python3
"""
Redis MCP Bridge - Bidirectional Claude Code <-> OpenClaw Communication
Uses Redis pub/sub for real-time messaging
"""

import asyncio
import json
import sys
import redis
import threading
import time
from datetime import datetime

# Redis configuration
REDIS_HOST = "77.42.66.40"
REDIS_PORT = 6379
REDIS_DB = 0

# Channel names
CHANNEL_CLAUDE_TO_OPENCLAW = "claude:openclaw:messages"
CHANNEL_OPENCLAW_TO_CLAUDE = "openclaw:claude:messages"
CHANNEL_RESPONSES = "claude:responses"

class RedisBridge:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()
        self.message_queue = []
        self.running = True

    def publish_to_openclaw(self, message, msg_type="text"):
        """Publish message from Claude Code to OpenClaw"""
        payload = {
            "from": "claude-code",
            "type": msg_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "id": f"claude-{int(time.time() * 1000)}"
        }
        self.redis_client.publish(CHANNEL_CLAUDE_TO_OPENCLAW, json.dumps(payload))
        return payload["id"]

    def listen_for_responses(self, callback):
        """Listen for messages from OpenClaw"""
        self.pubsub.subscribe(CHANNEL_OPENCLAW_TO_CLAUDE)
        print(f"[Redis Bridge] Subscribed to {CHANNEL_OPENCLAW_TO_CLAUDE}", file=sys.stderr)

        for message in self.pubsub.listen():
            if not self.running:
                break
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    callback(data)
                except json.JSONDecodeError:
                    callback({"raw": message['data']})

    def get_recent_messages(self, count=10):
        """Get recent messages from Redis list"""
        messages = self.redis_client.lrange(CHANNEL_RESPONSES, -count, -1)
        return [json.loads(m) for m in messages] if messages else []

    def close(self):
        self.running = False
        self.pubsub.unsubscribe()
        self.redis_client.close()

# Global bridge instance
bridge = RedisBridge()

async def main():
    print("[Redis Bridge] Starting...", file=sys.stderr)

    # Start listener in background thread
    def on_message(data):
        bridge.message_queue.append(data)
        print(f"[Redis Bridge] Received: {data}", file=sys.stderr)

    listener_thread = threading.Thread(
        target=bridge.listen_for_responses,
        args=(on_message,),
        daemon=True
    )
    listener_thread.start()

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
                            "name": "redis_send_to_openclaw",
                            "description": "Send message to OpenClaw via Redis",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "type": {"type": "string", "default": "text"}
                                },
                                "required": ["message"]
                            }
                        },
                        {
                            "name": "redis_receive_from_openclaw",
                            "description": "Receive messages from OpenClaw (poll for responses)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "timeout": {"type": "integer", "default": 10},
                                    "clear": {"type": "boolean", "default": true}
                                }
                            }
                        },
                        {
                            "name": "redis_conversation",
                            "description": "Send message and wait for response from OpenClaw",
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
                            "name": "redis_status",
                            "description": "Check Redis connection status",
                            "inputSchema": {"type": "object"}
                        }
                    ]
                }

            elif method == "tools/call":
                tool = request.get("params", {}).get("name", "")
                args = request.get("params", {}).get("arguments", {})

                if tool == "redis_send_to_openclaw":
                    message = args.get("message", "")
                    msg_type = args.get("type", "text")
                    msg_id = bridge.publish_to_openclaw(message, msg_type)
                    response = {
                        "content": [{
                            "type": "text",
                            "text": f"✅ Published to Redis (ID: {msg_id})"
                        }]
                    }

                elif tool == "redis_receive_from_openclaw":
                    timeout = args.get("timeout", 10)
                    clear = args.get("clear", True)

                    # Wait for messages
                    await asyncio.sleep(timeout)

                    # Get messages from queue
                    messages = bridge.message_queue.copy()
                    if clear:
                        bridge.message_queue.clear()

                    if messages:
                        text = json.dumps(messages, indent=2)
                    else:
                        text = "No messages received"

                    response = {"content": [{"type": "text", "text": text}]}

                elif tool == "redis_conversation":
                    message = args.get("message", "")
                    wait = args.get("wait_seconds", 15)

                    # Clear previous messages
                    bridge.message_queue.clear()

                    # Send message
                    msg_id = bridge.publish_to_openclaw(message)

                    # Wait for response
                    await asyncio.sleep(wait)

                    # Get responses
                    responses = bridge.message_queue.copy()
                    bridge.message_queue.clear()

                    result = f"📤 Sent: {message}\n📥 Responses ({len(responses)}):\n"
                    if responses:
                        result += json.dumps(responses, indent=2)
                    else:
                        result += "No response yet"

                    response = {"content": [{"type": "text", "text": result}]}

                elif tool == "redis_status":
                    try:
                        bridge.redis_client.ping()
                        status = "✅ Connected"
                    except Exception as e:
                        status = f"❌ Error: {e}"

                    response = {"content": [{"type": "text", "text": f"Redis Status: {status}"}]}

                else:
                    response = {
                        "content": [{"type": "text", "text": f"Unknown tool: {tool}"}],
                        "isError": True
                    }

            else:
                response = {"error": f"Unknown method: {method}"}

            response["jsonrpc"] = "2.0"
            response["id"] = msg_id
            print(json.dumps(response), flush=True)

        except Exception as e:
            error = {"jsonrpc": "2.0", "error": str(e), "id": request.get("id")}
            print(json.dumps(error), flush=True)

    bridge.close()

if __name__ == "__main__":
    asyncio.run(main())
