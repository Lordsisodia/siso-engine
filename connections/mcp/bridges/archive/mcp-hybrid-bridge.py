#!/usr/bin/env python3
"""
Hybrid Redis + NATS Bridge for Multi-Agent Communication
Combines Redis (state/cache) with NATS (messaging/persistence)
"""

import asyncio
import json
import sys
import redis
import threading
import time
from datetime import datetime

# NATS imports
try:
    import nats
    from nats.aio.client import Client as NATS
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False

# Configuration
REDIS_HOST = "77.42.66.40"
REDIS_PORT = 6379
NATS_HOST = "77.42.66.40"
NATS_PORT = 4222

class HybridBridge:
    def __init__(self, agent_id="claude-mac-01"):
        self.agent_id = agent_id
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        self.nats_client = None
        self.js = None  # JetStream context
        self.message_queue = []
        self.running = True

    async def connect_nats(self):
        """Connect to NATS server"""
        if not NATS_AVAILABLE:
            print("[Hybrid] NATS not available, using Redis only", file=sys.stderr)
            return False

        try:
            self.nats_client = await nats.connect(
                f"nats://{NATS_HOST}:{NATS_PORT}",
                reconnect_time_wait=2,
                max_reconnect_attempts=10
            )
            self.js = self.nats_client.jetstream()
            print(f"[Hybrid] Connected to NATS at {NATS_HOST}:{NATS_PORT}", file=sys.stderr)
            return True
        except Exception as e:
            print(f"[Hybrid] NATS connection failed: {e}", file=sys.stderr)
            return False

    # === Redis Methods (State & Cache) ===

    def redis_set_state(self, key, value):
        """Store state in Redis"""
        self.redis_client.hset(f"agent:{self.agent_id}:state", key, json.dumps(value))

    def redis_get_state(self, key):
        """Get state from Redis"""
        data = self.redis_client.hget(f"agent:{self.agent_id}:state", key)
        return json.loads(data) if data else None

    def redis_heartbeat(self):
        """Send heartbeat via Redis"""
        self.redis_client.setex(
            f"presence:{self.agent_id}",
            30,  # 30 second TTL
            datetime.utcnow().isoformat()
        )

    def redis_get_active_agents(self):
        """Get all active agents from Redis"""
        agents = []
        for key in self.redis_client.scan_iter(match="presence:*"):
            agent_id = key.decode().split(":")[1] if isinstance(key, bytes) else key.split(":")[1]
            agents.append(agent_id)
        return agents

    # === NATS Methods (Messaging) ===

    async def nats_publish_task(self, target_agent, task_data):
        """Publish task to NATS JetStream (guaranteed delivery)"""
        if not self.js:
            return False

        subject = f"tasks.{target_agent}"
        message = {
            "from": self.agent_id,
            "to": target_agent,
            "task": task_data,
            "timestamp": datetime.utcnow().isoformat(),
            "id": f"task-{int(time.time() * 1000)}"
        }

        try:
            await self.js.publish(subject, json.dumps(message).encode())
            return True
        except Exception as e:
            print(f"[Hybrid] NATS publish failed: {e}", file=sys.stderr)
            return False

    async def nats_subscribe_tasks(self, callback):
        """Subscribe to tasks for this agent"""
        if not self.js:
            return

        subject = f"tasks.{self.agent_id}"

        # Create consumer
        try:
            sub = await self.js.subscribe(subject)
            while self.running:
                try:
                    msg = await sub.next_msg(timeout=1.0)
                    data = json.loads(msg.data.decode())
                    callback(data)
                    await msg.ack()
                except asyncio.TimeoutError:
                    continue
        except Exception as e:
            print(f"[Hybrid] NATS subscribe error: {e}", file=sys.stderr)

    async def nats_broadcast(self, message_type, payload):
        """Broadcast message to all agents"""
        if not self.nats_client:
            return False

        message = {
            "from": self.agent_id,
            "type": message_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            await self.nats_client.publish("agents.broadcast", json.dumps(message).encode())
            return True
        except Exception as e:
            print(f"[Hybrid] NATS broadcast failed: {e}", file=sys.stderr)
            return False

    # === Hybrid Methods (Best of Both) ===

    async def send_message(self, target_agent, message, use_nats=True):
        """Send message to another agent (uses NATS if available, Redis fallback)"""
        if use_nats and self.js:
            # Use NATS for guaranteed delivery
            success = await self.nats_publish_task(target_agent, {"message": message})
            if success:
                return {"channel": "nats", "status": "sent"}

        # Fallback to Redis pub/sub
        self.redis_client.publish(
            f"agent:{target_agent}:inbox",
            json.dumps({"from": self.agent_id, "message": message})
        )
        return {"channel": "redis", "status": "sent"}

    async def get_agent_status(self, agent_id):
        """Get agent status (hybrid lookup)"""
        # Check Redis presence
        is_alive = self.redis_client.exists(f"presence:{agent_id}")

        # Get state from Redis
        state = self.redis_client.hgetall(f"agent:{agent_id}:state")

        return {
            "agent_id": agent_id,
            "alive": bool(is_alive),
            "state": {k: json.loads(v) for k, v in state.items()} if state else {}
        }

    async def start_heartbeat(self):
        """Start heartbeat loop"""
        while self.running:
            self.redis_heartbeat()
            await asyncio.sleep(10)  # Every 10 seconds

    async def close(self):
        """Cleanup"""
        self.running = False
        if self.nats_client:
            await self.nats_client.close()

# === MCP Server Interface ===

bridge = None

async def main():
    global bridge

    print("[Hybrid Bridge] Starting...", file=sys.stderr)

    # Initialize bridge
    bridge = HybridBridge(agent_id="claude-mac-01")

    # Connect to NATS
    nats_connected = await bridge.connect_nats()

    # Start heartbeat in background
    heartbeat_task = asyncio.create_task(bridge.start_heartbeat())

    # Start NATS subscriber if connected
    if nats_connected:
        def on_task(data):
            bridge.message_queue.append(data)
            print(f"[Hybrid] Received task: {data}", file=sys.stderr)

        nats_sub_task = asyncio.create_task(bridge.nats_subscribe_tasks(on_task))

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
                            "name": "hybrid_send_message",
                            "description": "Send message to another agent via NATS/Redis",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "target_agent": {"type": "string"},
                                    "message": {"type": "string"},
                                    "use_nats": {"type": "boolean", "default": True}
                                },
                                "required": ["target_agent", "message"]
                            }
                        },
                        {
                            "name": "hybrid_get_agents",
                            "description": "Get list of active agents",
                            "inputSchema": {"type": "object"}
                        },
                        {
                            "name": "hybrid_get_status",
                            "description": "Get status of specific agent",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "agent_id": {"type": "string"}
                                }
                            }
                        },
                        {
                            "name": "hybrid_broadcast",
                            "description": "Broadcast message to all agents",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message_type": {"type": "string"},
                                    "payload": {"type": "object"}
                                }
                            }
                        },
                        {
                            "name": "hybrid_store_state",
                            "description": "Store state in Redis",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "key": {"type": "string"},
                                    "value": {"type": "object"}
                                }
                            }
                        }
                    ]
                }

            elif method == "tools/call":
                tool = request.get("params", {}).get("name", "")
                args = request.get("params", {}).get("arguments", {})

                if tool == "hybrid_send_message":
                    target = args.get("target_agent")
                    message = args.get("message")
                    use_nats = args.get("use_nats", True)

                    result = await bridge.send_message(target, message, use_nats)
                    response = {"content": [{"type": "text", "text": json.dumps(result)}]}

                elif tool == "hybrid_get_agents":
                    agents = bridge.redis_get_active_agents()
                    response = {"content": [{"type": "text", "text": json.dumps({"agents": agents})}]}

                elif tool == "hybrid_get_status":
                    agent_id = args.get("agent_id", "all")
                    if agent_id == "all":
                        agents = bridge.redis_get_active_agents()
                        statuses = []
                        for aid in agents:
                            status = await bridge.get_agent_status(aid)
                            statuses.append(status)
                        response = {"content": [{"type": "text", "text": json.dumps(statuses)}]}
                    else:
                        status = await bridge.get_agent_status(agent_id)
                        response = {"content": [{"type": "text", "text": json.dumps(status)}]}

                elif tool == "hybrid_broadcast":
                    msg_type = args.get("message_type", "announcement")
                    payload = args.get("payload", {})

                    if bridge.nats_client:
                        success = await bridge.nats_broadcast(msg_type, payload)
                        response = {"content": [{"type": "text", "text": f"Broadcast via NATS: {success}"}]}
                    else:
                        response = {"content": [{"type": "text", "text": "NATS not connected"}]}

                elif tool == "hybrid_store_state":
                    key = args.get("key")
                    value = args.get("value")
                    bridge.redis_set_state(key, value)
                    response = {"content": [{"type": "text", "text": f"State stored: {key}"}]}

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

    await bridge.close()

if __name__ == "__main__":
    asyncio.run(main())
