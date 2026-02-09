#!/usr/bin/env python3
"""
Moltbot Simple MCP Server
You talk to Moltbot, Moltbot does things
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
CONFIG_FILE = os.path.expanduser("~/.blackbox5/moltbot-conversational.yaml")


def log(msg):
    print(f"[MOLTBOT] {msg}", file=sys.stderr)


def run_vps_command(cmd, timeout=60):
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
    """Load configuration"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        log(f"Error loading config: {e}")
        return {}


def get_workflow_status(workflow_name):
    """Check if workflow is running"""
    cmd = f"ps aux | grep '{workflow_name}' | grep -v grep | grep -v ssh"
    result = run_vps_command(cmd)
    if result.get("stdout"):
        lines = result["stdout"].strip().split('\n')
        return {"running": True, "instances": len(lines)}
    return {"running": False, "instances": 0}


def spawn_workflow(workflow_name, config):
    """Spawn a workflow process"""
    working_dir = config.get("working_dir", "/opt/ralf")
    command = config["command"]
    max_instances = config.get("max_instances", 1)

    # Check current instances
    status = get_workflow_status(workflow_name)
    if status["instances"] >= max_instances:
        return {"status": "skipped", "reason": f"Max instances ({max_instances}) already running"}

    # Build the full command
    log_file = f"/opt/moltbot/logs/{workflow_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    full_cmd = f"cd {working_dir} && nohup {command} > {log_file} 2>&1 &"

    result = run_vps_command(full_cmd)

    if result.get("returncode") == 0:
        return {"status": "spawned", "workflow": workflow_name, "log": log_file}
    else:
        return {"status": "failed", "error": result.get("stderr", "Unknown error")}


def stop_workflow(workflow_name):
    """Stop a running workflow"""
    cmd = f"pkill -f 'claude.*{workflow_name}'"
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
            status = get_workflow_status(name)
            workflow_list.append({
                "name": name,
                "description": wf_config.get("description", "No description"),
                "running": status["running"],
                "instances": status["instances"],
                "max_instances": wf_config.get("max_instances", 1)
            })

        return {"content": [{"type": "text", "text": json.dumps(workflow_list, indent=2)}]}

    elif tool_name == "moltbot_start_workflow":
        """Start a workflow"""
        workflow_name = args.get("workflow")
        config = load_config()

        if workflow_name not in config.get("workflows", {}):
            return {"content": [{"type": "text", "text": f"Unknown workflow: {workflow_name}"}], "isError": True}

        result = spawn_workflow(workflow_name, config["workflows"][workflow_name])

        if result["status"] == "spawned":
            send_telegram_message(f"🚀 Started workflow: {workflow_name}")
        elif result["status"] == "skipped":
            return {"content": [{"type": "text", "text": f"Workflow '{workflow_name}' already running ({result['reason']})"}]}
        else:
            return {"content": [{"type": "text", "text": f"Failed to start: {result.get('error')}"}], "isError": True}

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    elif tool_name == "moltbot_stop_workflow":
        """Stop a running workflow"""
        workflow_name = args.get("workflow")
        result = stop_workflow(workflow_name)
        send_telegram_message(f"🛑 Stopped workflow: {workflow_name}")
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    elif tool_name == "moltbot_workflow_status":
        """Get detailed status of workflows"""
        config = load_config()
        workflows = config.get("workflows", {})

        status_list = []
        for name, wf_config in workflows.items():
            status = get_workflow_status(name)
            status_list.append({
                "name": name,
                "status": "running" if status["running"] else "idle",
                "instances": status["instances"],
                "max_allowed": wf_config.get("max_instances", 1)
            })

        return {"content": [{"type": "text", "text": json.dumps(status_list, indent=2)}]}

    elif tool_name == "moltbot_send_message":
        """Send Telegram message"""
        message = args.get("message", "")
        result = send_telegram_message(message)
        return {"content": [{"type": "text", "text": result}]}

    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}


def main():
    log("Moltbot Simple MCP Server starting...")

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
                            "name": "moltbot-simple",
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
                                "name": "moltbot_list_workflows",
                                "description": "List all available workflows you can run",
                                "inputSchema": {"type": "object", "properties": {}}
                            },
                            {
                                "name": "moltbot_start_workflow",
                                "description": "Start a workflow by name",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "workflow": {"type": "string", "description": "Name of workflow to start (github-scout, codebase-audit, optimizer, execution-pool)"}
                                    },
                                    "required": ["workflow"]
                                }
                            },
                            {
                                "name": "moltbot_stop_workflow",
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
                                "name": "moltbot_workflow_status",
                                "description": "Check status of all workflows",
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
