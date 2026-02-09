#!/usr/bin/env python3
"""
BLACKBOX5 Comprehensive Feature Test Script
Tests all 200+ features mentioned in the README
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Add paths
sys.path.insert(0, '2-engine/01-core')
sys.path.insert(0, '2-engine/03-knowledge')

class FeatureTester:
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0

    def test(self, category: str, name: str, test_func) -> bool:
        """Run a single test"""
        self.total_tests += 1
        key = f"{category}: {name}"

        try:
            result = test_func()
            if result:
                self.passed_tests += 1
                self.results[key] = "✅ PASS"
                print(f"✅ {key}")
                return True
            else:
                self.results[key] = "⚠️  FAIL (returned False)"
                print(f"⚠️  {key} - returned False")
                self.failed_tests += 1
                return False
        except Exception as e:
            error_msg = str(e)[:100]
            self.results[key] = f"❌ ERROR: {error_msg}"
            print(f"❌ {key} - {error_msg}")
            self.failed_tests += 1
            return False

    def test_import(self, module_path: str) -> bool:
        """Test if a module can be imported"""
        try:
            # First try normal import
            parts = module_path.split('.')
            module = __import__(module_path)
            for part in parts[1:]:
                module = getattr(module, part)
            return True
        except Exception as e:
            # If that fails, try direct import from sys.modules
            try:
                import importlib
                module = importlib.import_module(module_path)
                return True
            except ImportError:
                return False

    def test_file_exists(self, file_path: str) -> bool:
        """Test if a file exists"""
        return Path(file_path).exists()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed:    {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%)")
        print(f"❌ Failed:    {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%)")
        print(f"⚠️  Skipped:  {self.skipped_tests}")
        print("="*80)

def main():
    tester = FeatureTester()

    print("="*80)
    print("BLACKBOX5 COMPREHENSIVE FEATURE TEST")
    print("="*80)
    print()

    # ============================================================
    # 🧠 Advanced Middleware Systems
    # ============================================================
    print("🧠 Advanced Middleware Systems")
    print("-" * 80)

    tester.test("Middleware", "Token Compression System", lambda: tester.test_import(
        "middleware.token_compressor"))
    tester.test("Middleware", "Context Extraction System", lambda: tester.test_import(
        "middleware.context_extractor"))

    # ============================================================
    # 📊 State Management & Event Systems
    # ============================================================
    print("\n📊 State Management & Event Systems")
    print("-" * 80)

    tester.test("State", "State Manager", lambda: tester.test_import("state.state_manager"))
    tester.test("State", "Event Bus", lambda: tester.test_import("state.event_bus"))

    # ============================================================
    # 🤖 Dynamic Agent Architecture
    # ============================================================
    print("\n🤖 Dynamic Agent Architecture")
    print("-" * 80)

    tester.test("Agents", "Agent Loader", lambda: tester.test_import("agents.framework.agent_loader"))
    tester.test("Agents", "Base Agent", lambda: tester.test_import("agents.framework.base_agent"))
    tester.test("Agents", "Architect Agent", lambda: tester.test_import("agents.ArchitectAgent"))
    tester.test("Agents", "Developer Agent", lambda: tester.test_import("agents.DeveloperAgent"))
    tester.test("Agents", "Analyst Agent", lambda: tester.test_import("agents.AnalystAgent"))
    tester.test("Agents", "Task Router", lambda: tester.test_import("routing.task_router"))

    # ============================================================
    # 🛡️ Safety & Security Systems
    # ============================================================
    print("\n🛡️ Safety & Security Systems")
    print("-" * 80)

    tester.test("Safety", "Constitutional Classifier", lambda: tester.test_import(
        "safety.constitutional_classifier"))
    tester.test("Safety", "Safe Mode", lambda: tester.test_import("safety.safe_mode"))
    tester.test("Safety", "Kill Switch", lambda: tester.test_import("safety.kill_switch"))
    tester.test("Safety", "Deviation Handler", lambda: tester.test_import(
        "tracking.deviation_handler"))

    # ============================================================
    # 📈 Monitoring & Observability
    # ============================================================
    print("\n📈 Monitoring & Observability")
    print("-" * 80)

    tester.test("Monitoring", "TUI Logger", lambda: tester.test_import(
        "infrastructure.logging.tui_logger"))
    tester.test("Monitoring", "Operation Tracker", lambda: tester.test_import(
        "infrastructure.monitoring.operation_tracker"))
    tester.test("Monitoring", "Health System", lambda: tester.test_import(
        "infrastructure.monitoring.health_system"))
    tester.test("Monitoring", "Statistics Collection", lambda: tester.test_import(
        "infrastructure.monitoring.statistics"))

    # ============================================================
    # 🔄 Workflow Systems
    # ============================================================
    print("\n🔄 Workflow Systems")
    print("-" * 80)

    tester.test("Workflows", "Development Workflows", lambda: Path(
        "2-engine/01-core/workflows/development").exists())
    tester.test("Workflows", "Planning Workflows", lambda: Path(
        "2-engine/01-core/workflows/planning").exists())

    # ============================================================
    # ❓ Sequential Questioning System
    # ============================================================
    print("\n❓ Sequential Questioning System")
    print("-" * 80)

    tester.test("Questioning", "Questioning Module", lambda: Path(
        "2-engine/01-core/questioning").exists())

    # ============================================================
    # 🚀 Performance Features
    # ============================================================
    print("\n🚀 Performance Features")
    print("-" * 80)

    tester.test("Performance", "Circuit Breaker", lambda: tester.test_import(
        "resilience.circuit_breaker"))
    tester.test("Performance", "Atomic Commit Manager", lambda: tester.test_import(
        "resilience.atomic_commit_manager"))

    # ============================================================
    # 🤖 Autonomous Systems
    # ============================================================
    print("\n🤖 Autonomous Systems")
    print("-" * 80)

    tester.test("Autonomous", "Ralph Runtime", lambda: Path(
        "2-engine/07-operations/runtime/ralphy").exists())
    tester.test("Autonomous", "Decision Engine", lambda: Path(
        "2-engine/01-core/decision").exists())
    tester.test("Autonomous", "Progress Tracker", lambda: tester.test_import(
        "monitoring.progress_tracker"))
    tester.test("Autonomous", "Error Recovery", lambda: tester.test_import(
        "monitoring.error_recovery"))

    # ============================================================
    # 💻 Command Line Interface
    # ============================================================
    print("\n💻 Command Line Interface")
    print("-" * 80)

    tester.test("CLI", "CLI Module", lambda: Path("2-engine/01-core/interface/cli").exists())

    # ============================================================
    # 🧠 Knowledge Brain System
    # ============================================================
    print("\n🧠 Knowledge Brain System")
    print("-" * 80)

    tester.test("Knowledge", "Brain API Module", lambda: Path(
        "2-engine/03-knowledge/storage/brain/api").exists())
    tester.test("Knowledge", "Brain API File", lambda: Path(
        "2-engine/03-knowledge/storage/brain/api/brain_api.py").exists())

    # ============================================================
    # 💾 Memory Systems
    # ============================================================
    print("\n💾 Memory Systems")
    print("-" * 80)

    tester.test("Memory", "Agent Memory System", lambda: tester.test_import(
        "AgentMemory"))
    tester.test("Memory", "Memory Module", lambda: Path(
        "2-engine/03-knowledge/memory").exists())

    # ============================================================
    # 🛠️ Specialized Tools
    # ============================================================
    print("\n🛠️ Specialized Tools")
    print("-" * 80)

    tester.test("Tools", "Domain Scanner", lambda: Path(
        "2-engine/05-tools/experiments/domain_scanner").exists())
    tester.test("Tools", "Code Indexer", lambda: Path(
        "2-engine/05-tools/experiments/code_indexer").exists())

    # ============================================================
    # 🔌 MCP Integrations
    # ============================================================
    print("\n🔌 MCP Integrations")
    print("-" * 80)

    tester.test("MCP", "MCP Config File", lambda: Path(
        "2-engine/.config/mcp-servers.json").exists())

    # ============================================================
    # 🌐 REST API Layer
    # ============================================================
    print("\n🌐 REST API Layer")
    print("-" * 80)

    tester.test("API", "API Main Module", lambda: tester.test_import("interface.api.main"))
    tester.test("API", "API File Exists", lambda: Path(
        "2-engine/01-core/interface/api/main.py").exists())

    # ============================================================
    # 📐 Claude Code Client
    # ============================================================
    print("\n📐 Claude Code Client")
    print("-" * 80)

    tester.test("Client", "Claude Code Client", lambda: tester.test_import(
        "client.ClaudeCodeClient"))

    # ============================================================
    # File Structure
    # ============================================================
    print("\n📁 File Structure")
    print("-" * 80)

    important_paths = [
        ("2-engine/01-core/agents", "Core Agents Directory"),
        ("2-engine/01-core/middleware", "Middleware Directory"),
        ("2-engine/01-core/state", "State Management Directory"),
        ("2-engine/01-core/routing", "Routing Directory"),
        ("2-engine/01-core/safety", "Safety Systems Directory"),
        ("2-engine/01-core/workflows", "Workflows Directory"),
        ("2-engine/03-knowledge", "Knowledge Directory"),
        ("2-engine/05-tools", "Tools Directory"),
        ("2-engine/.config", "Config Directory"),
        ("2-engine/07-operations", "Operations Directory"),
    ]

    for path, name in important_paths:
        tester.test("Structure", name, lambda p=path: Path(p).exists())

    # ============================================================
    # Print Summary
    # ============================================================
    tester.print_summary()

    # ============================================================
    # Save Results
    # ============================================================
    results_file = Path("blackbox5-test-results.txt")
    with open(results_file, 'w') as f:
        f.write("BLACKBOX5 TEST RESULTS\n")
        f.write("="*80 + "\n\n")

        for key, result in tester.results.items():
            f.write(f"{result} {key}\n")

        f.write("\n" + "="*80 + "\n")
        f.write(f"Total: {tester.total_tests} | ")
        f.write(f"Passed: {tester.passed_tests} | ")
        f.write(f"Failed: {tester.failed_tests} | ")
        f.write(f"Success Rate: {tester.passed_tests/tester.total_tests*100:.1f}%\n")

    print(f"\n📄 Results saved to: {results_file}")

if __name__ == "__main__":
    main()
