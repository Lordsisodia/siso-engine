#!/usr/bin/env python3
"""
MCP Bridge to Real Moltbot (OpenClaw) via WebSocket
Connects Claude Code to the actual AI running on VPS
"""

import asyncio
import json
import sys
import redis
import threading
import websockets
from datetime import datetime

# Configuration
REDIS_HOST = "77.42.66.40"
REDIS_PORT = 6379
MOLTBOT_WS = "ws://77.42.66.40:18789/ws"  # OpenClaw WebSocket
AGENT_ID = "moltbot-vps-01"

class MoltbotBridge:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()
        self.websocket = None
        self.running = True
        self.message_queue = []

    async def connect_websocket(self):
        """Connect to Moltbot WebSocket"""
        try:
            self.websocket = await websockets.connect(MOLTBOT_WS)
            print(f"[{AGENT_ID}] Connected to Moltbot WebSocket", file=sys.stderr)

            # Start listener
            asyncio.create_task(self.websocket_listener())
            return True
        except Exception as e:
            print(f"[{AGENT_ID}] WebSocket error: {e}", file=sys.stderr)
            return False

    async def websocket_listener(self):
        """Listen for messages from Moltbot"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                print(f"[{AGENT_ID}] From Moltbot: {data}", file=sys.stderr)

                # Forward to Redis
                response = {
                    "from": AGENT_ID,
                    "type": "response",
                    "message": data.get("message", ""),
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.redis_client.publish("openclaw:claude:messages", json.dumps(response))
        except Exception as e:
            print(f"[{AGENT_ID}] WebSocket listener error: {e}", file=sys.stderr)

    async def send_to_moltbot(self, message):
        """Send message to Moltbot via WebSocket"""
        if self.websocket:
            await self.websocket.send(json.dumps({
                "type": "message",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            }))
            return True
        return False

    def start(self):
        print(f"[{AGENT_ID}] Starting Moltbot Bridge...", file=sys.stderr)

        # Register agent
        self.register_agent()

        # Start heartbeat
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

        # Start Redis listener
        self.start_redis_listener()

    def register_agent(self):
        self.redis_client.hset(f"agent:{AGENT_ID}:info", mapping={
            "id": AGENT_ID,
            "type": "moltbot-ai",
            "capabilities": "ai_inference,nats_routing,websocket",
            "status": "ready",
            "version": "2.0.0",
            "ai_model": "GLM-4.7"
        })
        self.redis_client.sadd("registry:all", AGENT_ID)
        print(f"[{AGENT_ID}] Registered as real Moltbot AI", file=sys.stderr)

    def heartbeat_loop(self):
        while self.running:
            self.redis_client.setex(
                f"presence:{AGENT_ID}", 30, datetime.utcnow().isoformat()
            )
            time.sleep(10)

    def start_redis_listener(self):
        self.pubsub.subscribe("claude:openclaw:messages")
        print(f"[{AGENT_ID}] Listening on Redis", file=sys.stderr)

        for message in self.pubsub.listen():
            if not self.running:
                break

            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    if data.get("from") == AGENT_ID:
                        continue

                    print(f"[{AGENT_ID}] Redis: {data.get('message', '')}", file=sys.stderr)

                    # Forward to Moltbot
                    asyncio.run(self.send_to_moltbot(data.get("message", "")))

                except Exception as e:
                    print(f"[{AGENT_ID}] Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    bridge = MoltbotBridge()
    bridge.start()
