#!/usr/bin/env python3
"""
Agent Improvement Loop - Master Orchestration

Runs the complete improvement loop:
  Scout → Planner → Executor → Verifier

Usage:
    improvement-loop.py [--scout] [--planner] [--executor] [--verifier] [--all]
    improvement-loop.py --continuous --interval MINUTES
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configuration
PROJECT_DIR = Path.home() / ".blackbox5" / "5-project-memory" / "blackbox5"
ENGINE_DIR = Path.home() / ".blackbox5" / "2-engine"
BIN_DIR = ENGINE_DIR / ".autonomous" / "bin"
REPORTS_DIR = PROJECT_DIR / ".autonomous" / "analysis"


class ImprovementLoop:
    """
    Master orchestrator for the Agent Improvement Loop.
    """

    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.start_time: Optional[datetime] = None

    def log(self, message: str):
        """Print with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_scout(self) -> bool:
        """Run the Scout Agent to find opportunities."""
        self.log("\n" + "="*60)
        self.log("PHASE 1: SCOUT - Finding Opportunities")
        self.log("="*60)

        scout_script = BIN_DIR / "scout-intelligent.py"

        if not scout_script.exists():
            self.log(f"❌ Scout script not found: {scout_script}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(scout_script), "--parallel"],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                cwd=str(PROJECT_DIR)
            )

            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            success = result.returncode == 0
            self.results["scout"] = {"success": success, "output": result.stdout}
            return success

        except subprocess.TimeoutExpired:
            self.log("⏱️ Scout timed out after 10 minutes")
            return False
        except Exception as e:
            self.log(f"❌ Scout failed: {e}")
            return False

    def run_planner(self) -> bool:
        """Run the Planner Agent to prioritize opportunities."""
        self.log("\n" + "="*60)
        self.log("PHASE 2: PLANNER - Prioritizing Opportunities")
        self.log("="*60)

        planner_script = BIN_DIR / "planner-prioritize.py"

        if not planner_script.exists():
            self.log(f"❌ Planner script not found: {planner_script}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(planner_script)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(PROJECT_DIR)
            )

            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            success = result.returncode == 0
            self.results["planner"] = {"success": success, "output": result.stdout}
            return success

        except Exception as e:
            self.log(f"❌ Planner failed: {e}")
            return False

    def run_executor(self, quick_wins_only: bool = True, limit: int = 5) -> bool:
        """Run the Executor Agent to implement improvements."""
        self.log("\n" + "="*60)
        self.log("PHASE 3: EXECUTOR - Implementing Improvements")
        self.log("="*60)

        executor_script = BIN_DIR / "executor-implement.py"

        if not executor_script.exists():
            self.log(f"❌ Executor script not found: {executor_script}")
            return False

        try:
            cmd = [sys.executable, str(executor_script)]
            if quick_wins_only:
                cmd.extend(["--quick-wins", "--limit", str(limit)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(PROJECT_DIR)
            )

            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            success = result.returncode == 0
            self.results["executor"] = {"success": success, "output": result.stdout}
            return success

        except Exception as e:
            self.log(f"❌ Executor failed: {e}")
            return False

    def run_verifier(self) -> bool:
        """Run the Verifier Agent to validate improvements."""
        self.log("\n" + "="*60)
        self.log("PHASE 4: VERIFIER - Validating Improvements")
        self.log("="*60)

        verifier_script = BIN_DIR / "verifier-validate.py"

        if not verifier_script.exists():
            self.log(f"❌ Verifier script not found: {verifier_script}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(verifier_script), "--latest"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(PROJECT_DIR)
            )

            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            success = result.returncode == 0
            self.results["verifier"] = {"success": success, "output": result.stdout}
            return success

        except Exception as e:
            self.log(f"❌ Verifier failed: {e}")
            return False

    def save_loop_report(self) -> Path:
        """Save the complete loop execution report."""
        report_dir = REPORTS_DIR / "loop-reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_id = f"LOOP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Calculate duration
        duration = None
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()

        report = {
            "improvement_loop_report": {
                "id": report_id,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": duration,
                "phases": {
                    "scout": self.results.get("scout", {}).get("success", False),
                    "planner": self.results.get("planner", {}).get("success", False),
                    "executor": self.results.get("executor", {}).get("success", False),
                    "verifier": self.results.get("verifier", {}).get("success", False)
                },
                "overall_success": all(
                    self.results.get(phase, {}).get("success", False)
                    for phase in ["scout", "planner", "executor", "verifier"]
                )
            }
        }

        # Save JSON
        json_file = report_dir / f"{report_id}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.log(f"\n✅ Loop report saved: {json_file}")
        return json_file

    def print_summary(self):
        """Print execution summary."""
        print("\n" + "="*60)
        print("AGENT IMPROVEMENT LOOP - EXECUTION SUMMARY")
        print("="*60)

        phases = ["scout", "planner", "executor", "verifier"]
        for phase in phases:
            result = self.results.get(phase, {})
            status = "✅" if result.get("success", False) else "❌"
            print(f"   {status} {phase.capitalize()}")

        overall = all(
            self.results.get(phase, {}).get("success", False)
            for phase in phases
        )

        print(f"\n   Overall: {'✅ SUCCESS' if overall else '❌ PARTIAL'}")
        print("="*60)

    def run_full_loop(self, skip_scout: bool = False, skip_planner: bool = False,
                     skip_executor: bool = False, skip_verifier: bool = False) -> bool:
        """Run the complete improvement loop."""
        self.start_time = datetime.now()

        self.log("\n🚀 Starting Agent Improvement Loop")
        self.log(f"   Project: {PROJECT_DIR}")
        self.log(f"   Time: {self.start_time.isoformat()}")

        # Phase 1: Scout
        if not skip_scout:
            if not self.run_scout():
                self.log("⚠️ Scout phase failed, continuing...")

        # Phase 2: Planner
        if not skip_planner:
            if not self.run_planner():
                self.log("⚠️ Planner phase failed, continuing...")

        # Phase 3: Executor
        if not skip_executor:
            if not self.run_executor(quick_wins_only=True, limit=5):
                self.log("⚠️ Executor phase failed, continuing...")

        # Phase 4: Verifier
        if not skip_verifier:
            if not self.run_verifier():
                self.log("⚠️ Verifier phase failed, continuing...")

        # Save report
        self.save_loop_report()

        # Print summary
        self.print_summary()

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Agent Improvement Loop - Master Orchestration"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all phases"
    )
    parser.add_argument(
        "--scout",
        action="store_true",
        help="Run Scout phase only"
    )
    parser.add_argument(
        "--planner",
        action="store_true",
        help="Run Planner phase only"
    )
    parser.add_argument(
        "--executor",
        action="store_true",
        help="Run Executor phase only"
    )
    parser.add_argument(
        "--verifier",
        action="store_true",
        help="Run Verifier phase only"
    )
    parser.add_argument(
        "--skip-scout",
        action="store_true",
        help="Skip Scout phase"
    )
    parser.add_argument(
        "--skip-planner",
        action="store_true",
        help="Skip Planner phase"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval between runs in minutes (for continuous mode)"
    )

    args = parser.parse_args()

    loop = ImprovementLoop()

    if args.all:
        loop.run_full_loop()
    elif args.scout:
        loop.run_scout()
    elif args.planner:
        loop.run_planner()
    elif args.executor:
        loop.run_executor()
    elif args.verifier:
        loop.run_verifier()
    elif args.continuous:
        print(f"🔄 Continuous mode: Running every {args.interval} minutes")
        print("   Press Ctrl+C to stop\n")
        try:
            while True:
                loop.run_full_loop()
                print(f"\n⏳ Sleeping for {args.interval} minutes...")
                time.sleep(args.interval * 60)
        except KeyboardInterrupt:
            print("\n\n👋 Stopping continuous loop")
    else:
        # Default: run full loop
        loop.run_full_loop(
            skip_scout=args.skip_scout,
            skip_planner=args.skip_planner
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
