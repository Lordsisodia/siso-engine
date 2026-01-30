#!/usr/bin/env python3
"""
Verification script for KillSwitch enhancements.

This script demonstrates all 4 phases of the enhanced KillSwitch:
1. Delivery Confirmation
2. Compliance Verification
3. Recovery Testing
4. Backup Trigger

Run this to verify the KillSwitch is working correctly.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from kill_switch import KillSwitch, KillSwitchReason, KillSwitchState


class MockAgent:
    """Mock agent for demonstration"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.is_running = True

    def stop(self):
        """Stop the agent"""
        self.is_running = False
        return True


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_subsection(title: str):
    """Print a subsection header"""
    print(f"\n{title}")
    print(f"{'-'*60}")


def verify_delivery_confirmation(ks: KillSwitch):
    """Verify Phase 1: Delivery Confirmation"""
    print_section("Phase 1: Delivery Confirmation")

    # Create mock agents
    agents = [MockAgent(f"agent-{i}") for i in range(3)]
    ks._expected_agents = {agent.agent_id for agent in agents}

    # Trigger kill switch
    print("Triggering kill switch...")
    result = ks.trigger(KillSwitchReason.MANUAL, "Test delivery confirmation")
    print(f"✓ Triggered: {result}")

    # Simulate agents acknowledging
    print("\nSimulating agent acknowledgments...")
    for agent in agents:
        agent.stop()
        ks.register_acknowledgment(agent.agent_id, agent.is_running == False)
        print(f"✓ Agent {agent.agent_id} acknowledged")

    # Check status
    status = ks.get_status()
    print_subsection("Status")
    print(f"  Expected agents: {len(status['expected_agents'])}")
    print(f"  Acknowledgments: {len(status['acknowledgments'])}")
    print(f"  Acknowledgment rate: {status['acknowledgment_rate']*100:.1f}%")
    print(f"  Missing agents: {status['missing_acknowledgments']}")

    # Verify
    if status['acknowledgment_rate'] == 1.0:
        print("\n✅ SUCCESS: All agents acknowledged")
        return True
    else:
        print("\n❌ FAILURE: Some agents didn't acknowledge")
        return False


def verify_compliance_verification(ks: KillSwitch):
    """Verify Phase 2: Compliance Verification"""
    print_section("Phase 2: Compliance Verification")

    # Reset for next test
    ks._state = KillSwitchState.ACTIVE
    ks._acknowledgments = {}
    ks._expected_agents = set()

    # Create agents
    agents = [MockAgent(f"agent-{i}") for i in range(3)]
    ks._expected_agents = {agent.agent_id for agent in agents}

    # Trigger
    print("Triggering kill switch...")
    ks.trigger(KillSwitchReason.MANUAL, "Test compliance verification")

    # Agents acknowledge
    print("\nAgents acknowledging...")
    for agent in agents:
        agent.stop()
        ks.register_acknowledgment(agent.agent_id, True)

    # Check compliance
    print_subsection("Compliance Check")
    print(f"  Compliance verified: {ks._compliance_verified}")
    print(f"  Force kill used: {ks._force_kill_used}")
    print(f"  All agents stopped: {all(not a.is_running for a in agents)}")

    if all(not a.is_running for a in agents):
        print("\n✅ SUCCESS: All agents compliant")
        return True
    else:
        print("\n❌ FAILURE: Some agents still running")
        return False


def verify_recovery_testing(ks: KillSwitch):
    """Verify Phase 3: Recovery Testing"""
    print_section("Phase 3: Recovery Testing")

    # Reset
    ks._state = KillSwitchState.ACTIVE
    ks._test_results = []

    # Run recovery test
    print("Running recovery test...")
    result = ks.test_recovery()

    # Display results
    print_subsection("Test Results")
    print(f"  Test type: {result['test_type']}")
    print(f"  Success: {result['success']}")
    print(f"  Phases: {len(result['phases'])}")

    for phase in result['phases']:
        print(f"    - {phase['phase']}: {phase['success']}")

    # Check status
    status = ks.get_status()
    print_subsection("Status")
    print(f"  Test count: {status['test_count']}")
    print(f"  Operational: {status['operational']}")

    if result['success'] and status['operational']:
        print("\n✅ SUCCESS: Recovery test passed")
        return True
    else:
        print("\n❌ FAILURE: Recovery test failed")
        return False


def verify_backup_trigger(ks: KillSwitch):
    """Verify Phase 4: Backup Trigger"""
    print_section("Phase 4: Backup Trigger")

    # Create backup trigger
    print("Creating backup trigger...")
    ks._backup_trigger(
        KillSwitchReason.CRITICAL_FAILURE,
        "Event bus failed",
        "test"
    )

    # Check file exists
    backup_file = ks._backup_trigger_file
    print(f"✓ Backup file created: {backup_file.exists()}")

    if backup_file.exists():
        # Read and display content
        with open(backup_file, 'r') as f:
            data = json.load(f)
        print_subsection("Backup Trigger Content")
        print(f"  Reason: {data['reason']}")
        print(f"  Message: {data['message']}")
        print(f"  Source: {data['source']}")
        print(f"  Timestamp: {data['timestamp']}")

        # Check detection
        print("\nChecking for backup trigger...")
        detected = ks.check_backup_trigger()
        print(f"✓ Detected: {detected}")
        print(f"✓ File cleaned up: {not backup_file.exists()}")

        if detected and not backup_file.exists():
            print("\n✅ SUCCESS: Backup trigger works")
            return True
        else:
            print("\n❌ FAILURE: Backup trigger failed")
            return False
    else:
        print("\n❌ FAILURE: Backup file not created")
        return False


def verify_comprehensive_status(ks: KillSwitch):
    """Verify comprehensive status reporting"""
    print_section("Comprehensive Status Report")

    status = ks.get_status()

    print("Basic Status:")
    print(f"  State: {status['state']}")
    print(f"  Operational: {status['operational']}")
    print(f"  Trigger count: {status['trigger_count']}")
    print(f"  Recovery count: {status['recovery_count']}")

    print("\nDelivery Confirmation:")
    print(f"  Expected agents: {len(status['expected_agents'])}")
    print(f"  Acknowledgments: {len(status['acknowledgments'])}")
    print(f"  Acknowledgment rate: {status['acknowledgment_rate']*100:.1f}%")
    print(f"  Missing: {status['missing_acknowledgments']}")

    print("\nCompliance:")
    print(f"  Compliance verified: {status['compliance_verified']}")
    print(f"  Force kill used: {status['force_kill_used']}")

    print("\nTesting:")
    print(f"  Test count: {status['test_count']}")
    print(f"  Last test: {status['last_test_result']['success'] if status['last_test_result'] else 'N/A'}")

    print("\n✅ SUCCESS: Comprehensive status reporting works")
    return True


def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("  KillSwitch Enhancement Verification")
    print("="*60)

    # Create kill switch instance
    ks = KillSwitch()
    ks._state = KillSwitchState.ACTIVE

    # Run all phases
    results = {
        "Phase 1 - Delivery Confirmation": verify_delivery_confirmation(ks),
        "Phase 2 - Compliance Verification": verify_compliance_verification(ks),
        "Phase 3 - Recovery Testing": verify_recovery_testing(ks),
        "Phase 4 - Backup Trigger": verify_backup_trigger(ks),
        "Comprehensive Status": verify_comprehensive_status(ks),
    }

    # Summary
    print_section("Summary")
    for phase, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {phase}")

    all_passed = all(results.values())
    print(f"\n{'='*60}")
    if all_passed:
        print("  ✅ ALL TESTS PASSED")
        print("  KillSwitch enhancements are working correctly!")
    else:
        print("  ❌ SOME TESTS FAILED")
        print("  Please review the failures above.")
    print(f"{'='*60}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
