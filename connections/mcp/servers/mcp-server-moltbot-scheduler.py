#!/usr/bin/env python3
"""
Moltbot Hybrid Scheduler MCP Server
Smart scheduling without micro-management
"""

import json
import sys
import subprocess
import os
import yaml
from datetime import datetime

VPS_IP = "77.42.66.40"
VPS_USER = "root"
SSH_KEY = os.path.expanduser("~/.ssh/ralf_hetzner")
SCHEDULER_CONFIG = os.path.expanduser("~/.blackbox5/moltbot-scheduler.yaml")


def log(msg):
    print(f"[MOLTBOT-SCHEDULER] {msg}", file=sys.stderr)


def run_vps_command(cmd, timeout=30):
    """Run a command on the VPS via SSH"""
    try:
        result = subprocess.run(
            ["ssh", "-i", SSH_KEY, f"{VPS_USER}@{VPS_IP}", cmd],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}


def load_config():
    """Load scheduler configuration"""
    try:
        with open(SCHEDULER_CONFIG, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        log(f"Error loading config: {e}")
        return {}


def get_workflow_status(workflow_name):
    """Check if workflow is running"""
    cmd = f"ps aux | grep '{workflow_name}' | grep -v grep"
    result = run_vps_command(cmd)
    return "running" if result.get("stdout") else "idle"


def get_system_metrics():
    """Get CPU and memory usage from VPS"""
    cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
    mem_cmd = "free | grep Mem | awk '{print ($3/$2) * 100.0}'"

    cpu_result = run_vps_command(cpu_cmd)
    mem_result = run_vps_command(mem_cmd)

    try:
        cpu = float(cpu_result.get("stdout", 0))
        memory = float(mem_result.get("stdout", 0))
    except:
        cpu, memory = 0, 0

    return {"cpu": cpu, "memory": memory}


def get_queue_depth():
    """Get number of pending tasks in queue"""
    cmd = "grep -c 'status: pending' /opt/ralf/5-project-memory/blackbox5/.autonomous/agents/communications/queue.yaml 2>/dev/null || echo 0"
    result = run_vps_command(cmd)
    try:
        return int(result.get("stdout", 0))
    except:
        return 0


def spawn_workflow(workflow_name, config):
    """Spawn a workflow process"""
    working_dir = config.get("working_dir", "/opt/ralf")
    command = config["command"]

    # Build the full command
    full_cmd = f"cd {working_dir} && nohup {command} > /opt/moltbot/logs/{workflow_name}.log 2>&1 &"

    result = run_vps_command(full_cmd)

    if result.get("returncode") == 0:
        return {"status": "spawned", "workflow": workflow_name}
    else:
        return {"status": "failed", "error": result.get("stderr")}


def stop_workflow(workflow_name):
    """Stop a running workflow"""
    cmd = f"pkill -f '{workflow_name}'"
    result = run_vps_command(cmd)
    return {"status": "stopped", "workflow": workflow_name}


def send_telegram_message(message):
    """Send a message via Telegram bot"""
    cmd = f'openclaw message send --channel telegram --target 7643203581 --message "{message}" 2>&1'
    result = run_vps_command(cmd)
    return result.get("stdout", "No output")


def handle_tool_call(tool_name, args):
    """Handle MCP tool calls"""

    if tool_name == "moltbot_list_workflows":
        """List all available workflows"""
        config = load_config()
        workflows = config.get("workflows", {})

        workflow_list = []
        for name, wf_config in workflows.items():
            workflow_list.append({
                "name": name,
                "description": wf_config.get("description", "No description"),
                "status": get_workflow_status(name)
            })

        return {"content": [{"type": "text", "text": json.dumps(workflow_list, indent=2)}]}

    elif tool_name == "moltbot_workflow_status":
        """Get status of all workflows"""
        config = load_config()
        workflows = config.get("workflows", {})
        metrics = get_system_metrics()
        queue_depth = get_queue_depth()

        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": metrics,
            "queue_depth": queue_depth,
            "workflows": {}
        }

        for name, wf_config in workflows.items():
            status["workflows"][name] = {
                "status": get_workflow_status(name),
                "schedule": wf_config.get("schedule", "on-demand"),
                "conditions": wf_config.get("conditions", {})
            }

        return {"content": [{"type": "text", "text": json.dumps(status, indent=2)}]}

    elif tool_name == "moltbot_scheduler_spawn":
        """Manually spawn a workflow"""
        workflow_name = args.get("workflow")
        config = load_config()

        if workflow_name not in config.get("workflows", {}):
            return {"content": [{"type": "text", "text": f"Unknown workflow: {workflow_name}"}], "isError": True}

        result = spawn_workflow(workflow_name, config["workflows"][workflow_name])

        if result["status"] == "spawned":
            send_telegram_message(f"🚀 Workflow '{workflow_name}' manually started")

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    elif tool_name == "moltbot_scheduler_stop":
        """Stop a running workflow"""
        workflow_name = args.get("workflow")
        result = stop_workflow(workflow_name)
        send_telegram_message(f"🛑 Workflow '{workflow_name}' manually stopped")
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    elif tool_name == "moltbot_scheduler_evaluate":
        """Evaluate if workflows should run based on conditions"""
        config = load_config()
        workflows = config.get("workflows", {})
        metrics = get_system_metrics()
        queue_depth = get_queue_depth()

        recommendations = []

        for name, wf_config in workflows.items():
            current_status = get_workflow_status(name)
            conditions = wf_config.get("conditions", {})

            # Check if already running
            if current_status == "running":
                continue

            # Check CPU threshold
            cpu_threshold = conditions.get("cpu_threshold", 100)
            if metrics["cpu"] > cpu_threshold:
                recommendations.append({
                    "workflow": name,
                    "action": "skip",
                    "reason": f"CPU {metrics['cpu']}% > threshold {cpu_threshold}%"
                })
                continue

            # Check queue depth trigger
            if wf_config.get("trigger") == "queue_depth":
                min_depth = conditions.get("min_queue_depth", 1)
                if queue_depth < min_depth:
                    recommendations.append({
                        "workflow": name,
                        "action": "skip",
                        "reason": f"Queue depth {queue_depth} < minimum {min_depth}"
                    })
                    continue

            # Check if other workflows running
            skip_if_running = conditions.get("skip_if_running", [])
            conflicts = [w for w in skip_if_running if get_workflow_status(w) == "running"]
            if conflicts:
                recommendations.append({
                    "workflow": name,
                    "action": "skip",
                    "reason": f"Conflicts running: {conflicts}"
                })
                continue

            # All conditions met
            recommendations.append({
                "workflow": name,
                "action": "spawn",
                "reason": "All conditions met"
            })

        return {"content": [{"type": "text", "text": json.dumps(recommendations, indent=2)}]}

    elif tool_name == "moltbot_send_message":
        """Send Telegram message"""
        message = args.get("message", "")
        result = send_telegram_message(message)
        return {"content": [{"type": "text", "text": result}]}

    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}


def main():
    log("Moltbot Hybrid Scheduler MCP Server starting...")

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
                        "serverInfo": {
                            "name": "moltbot-scheduler",
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
                                "name": "moltbot_scheduler_status",
                                "description": "Get status of all workflows and system metrics",
                                "inputSchema": {"type": "object", "properties": {}}
                            },
                            {
                                "name": "moltbot_scheduler_spawn",
                                "description": "Manually spawn a workflow",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "workflow": {"type": "string", "description": "Name of workflow to spawn"}
                                    },
                                    "required": ["workflow"]
                                }
                            },
                            {
                                "name": "moltbot_scheduler_stop",
                                "description": "Stop a running workflow",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "workflow": {"type": "string", "description": "Name of workflow to stop"}
                                    },
                                    "required": ["workflow"]
                                }
                            },
                            {
                                "name": "moltbot_scheduler_evaluate",
                                "description": "Evaluate which workflows should run based on conditions",
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
