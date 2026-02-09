#!/usr/bin/env python3
"""
Real Moltbot Bridge - Connects to actual OpenClaw AI via CLI
This talks to the REAL AI (GLM 4.7), not a simple echo
"""

import asyncio
import json
import sys
import redis
import subprocess
import threading
import time
from datetime import datetime

REDIS_HOST = "77.42.66.40"
REDIS_PORT = 6379
AGENT_ID = "moltbot-vps-ai"
SESSION_ID = "redis-bridge-session"

class RealMoltbotBridge:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()
        self.running = True

    def start(self):
        print(f"[{AGENT_ID}] Starting REAL Moltbot Bridge...", file=sys.stderr)
        print(f"[{AGENT_ID}] This connects to GLM 4.7 AI", file=sys.stderr)

        self.register_agent()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        self.start_redis_listener()

    def register_agent(self):
        self.redis_client.hset(f"agent:{AGENT_ID}:info", mapping={
            "id": AGENT_ID,
            "type": "moltbot-ai",
            "ai_model": "GLM-4.7",
            "capabilities": "ai_inference,reasoning,code_generation",
            "status": "ready",
            "real_ai": "true"
        })
        self.redis_client.sadd("registry:all", AGENT_ID)
        self.redis_client.sadd("registry:type:moltbot-ai", AGENT_ID)
        print(f"[{AGENT_ID}] Registered as REAL AI", file=sys.stderr)

    def heartbeat_loop(self):
        while self.running:
            self.redis_client.setex(
                f"presence:{AGENT_ID}", 30, datetime.utcnow().isoformat()
            )
            time.sleep(10)

    def query_real_ai(self, message):
        """Query the real Moltbot AI via CLI"""
        try:
            # Use OpenClaw CLI to talk to real AI
            cmd = [
                "ssh", "-i", "/Users/shaansisodia/.ssh/ralf_hetzner",
                "root@77.42.66.40",
                f'echo "{message.replace(chr(34), chr(92)+chr(34))}" | openclaw agent --local --message - --session-id {SESSION_ID}'
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
            elif result.stderr:
                return f"AI Error: {result.stderr.strip()}"
            else:
                return "(AI did not respond)"

        except subprocess.TimeoutExpired:
            return "(AI response timeout)"
        except Exception as e:
            return f"(Error querying AI: {e})"

    def start_redis_listener(self):
        self.pubsub.subscribe("claude:openclaw:messages")
        print(f"[{AGENT_ID}] Listening for messages...", file=sys.stderr)

        for message in self.pubsub.listen():
            if not self.running:
                break

            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    if data.get("from") == AGENT_ID:
                        continue

                    from_agent = data.get("from", "unknown")
                    msg_text = data.get("message", "")
                    msg_id = data.get("id", "")

                    print(f"[{AGENT_ID}] From {from_agent}: {msg_text[:50]}...", file=sys.stderr)
                    print(f"[{AGENT_ID}] Querying real AI...", file=sys.stderr)

                    # Query the REAL AI
                    ai_response = self.query_real_ai(msg_text)

                    print(f"[{AGENT_ID}] AI responded: {ai_response[:100]}...", file=sys.stderr)

                    # Send response
                    response = {
                        "from": AGENT_ID,
                        "type": "response",
                        "message": ai_response,
                        "in_reply_to": msg_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "ai_model": "GLM-4.7",
                        "real_ai": True
                    }

                    self.redis_client.publish("openclaw:claude:messages", json.dumps(response))

                except Exception as e:
                    print(f"[{AGENT_ID}] Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    bridge = RealMoltbotBridge()
    bridge.start()
