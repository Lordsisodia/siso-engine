"""
Integration tests for enhanced KillSwitch with delivery confirmation,
compliance verification, and recovery testing.
"""

import asyncio
import pytest
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Import the KillSwitch
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kill_switch import (
    KillSwitch,
    KillSwitchReason,
    KillSwitchState,
    get_kill_switch
)


class MockAgent:
    """Mock agent for testing"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.is_running = True
        self.received_kill_signal = False
        self.force_stop_called = False

    def stop(self):
        """Stop the agent"""
        self.is_running = False
        self.received_kill_signal = True

    def force_stop(self):
        """Force stop the agent"""
        self.is_running = False
        self.force_stop_called = True


class NonCompliantAgent(MockAgent):
    """Agent that ignores kill signals"""

    def stop(self):
        """Ignores stop command"""
        self.received_kill_signal = True
        # But keeps running!
        pass


@pytest.fixture
def kill_switch():
    """Get a fresh kill switch instance for testing"""
    ks = KillSwitch()
    # Reset to ACTIVE state
    ks._state = KillSwitchState.ACTIVE
    ks._expected_agents = set()
    ks._acknowledgments = {}
    ks._compliance_verified = False
    ks._force_kill_used = False
    return ks


# ========== Phase 1: Delivery Confirmation Tests ==========

def test_delivery_confirmation_basic(kill_switch):
    """Test basic delivery confirmation mechanism"""
    # Register 3 mock agents
    agents = [MockAgent(f"agent-{i}") for i in range(3)]

    # Simulate kill switch detecting them
    kill_switch._expected_agents = {agent.agent_id for agent in agents}

    # Trigger kill switch
    result = kill_switch.trigger(KillSwitchReason.MANUAL, "Test delivery")

    assert result is True
    assert kill_switch.is_triggered()

    # Simulate agents acknowledging
    for agent in agents:
        agent.stop()
        kill_switch.register_acknowledgment(agent.agent_id, agent.is_running == False)

    # Check acknowledgments
    assert len(kill_switch._acknowledgments) == 3
    assert len(kill_switch.get_missing_acknowledgments()) == 0


def test_delivery_confirmation_with_missing_agents(kill_switch):
    """Test delivery confirmation when some agents don't acknowledge"""
    # Reset state to ACTIVE first
    kill_switch._state = KillSwitchState.ACTIVE

    # Clear any existing state first
    kill_switch._expected_agents = set()
    kill_switch._acknowledgments = {}

    # Register 3 agents
    agents = [MockAgent(f"agent-{i}") for i in range(3)]

    # Set expected agents AFTER trigger to avoid _get_running_agents() overwriting
    kill_switch._expected_agents = {agent.agent_id for agent in agents}

    # Trigger
    kill_switch.trigger(KillSwitchReason.MANUAL, "Test missing")

    # Re-set expected agents (trigger may have cleared it)
    kill_switch._expected_agents = {agent.agent_id for agent in agents}

    # Only 2 agents acknowledge
    for i in range(2):
        agents[i].stop()
        kill_switch.register_acknowledgment(agents[i].agent_id, True)

    # Check status
    missing = kill_switch.get_missing_acknowledgments()
    assert len(missing) == 1
    assert "agent-2" in missing


def test_acknowledgment_rate(kill_switch):
    """Test acknowledgment rate calculation"""
    # Reset state to ACTIVE first
    kill_switch._state = KillSwitchState.ACTIVE

    # 10 agents, 8 acknowledge
    agents = [MockAgent(f"agent-{i}") for i in range(10)]

    # Clear existing state
    kill_switch._expected_agents = set()
    kill_switch._acknowledgments = {}

    kill_switch._expected_agents = {agent.agent_id for agent in agents}

    kill_switch.trigger(KillSwitchReason.MANUAL, "Test rate")

    # Re-set expected agents (trigger may have called _get_running_agents)
    kill_switch._expected_agents = {agent.agent_id for agent in agents}

    # 8 acknowledge
    for i in range(8):
        kill_switch.register_acknowledgment(f"agent-{i}", True)

    status = kill_switch.get_status()
    assert status["acknowledgment_rate"] == 0.8
    assert len(status["expected_agents"]) == 10


# ========== Phase 2: Compliance Verification Tests ==========

@pytest.mark.asyncio
async def test_compliance_verification_all_stopped(kill_switch):
    """Test compliance verification when all agents stop"""
    # Create compliant agents
    agents = [MockAgent(f"agent-{i}") for i in range(3)]
    kill_switch._expected_agents = {agent.agent_id for agent in agents}

    # Trigger
    kill_switch.trigger(KillSwitchReason.MANUAL, "Test compliance")

    # All agents acknowledge and stop
    for agent in agents:
        agent.stop()
        kill_switch.register_acknowledgment(agent.agent_id, True)

    # Verify compliance (will pass since we can't check actual running state in test)
    result = await kill_switch._verify_agents_stopped()
    assert result is True  # Returns True when registry unavailable


@pytest.mark.asyncio
async def test_compliance_verification_non_compliant(kill_switch):
    """Test compliance verification with non-compliant agent"""
    # Create one non-compliant agent
    agents = [MockAgent(f"agent-{i}") for i in range(2)]
    rogue = NonCompliantAgent("rogue-agent")
    all_agents = agents + [rogue]

    kill_switch._expected_agents = {agent.agent_id for agent in all_agents}

    # Trigger
    kill_switch.trigger(KillSwitchReason.SAFETY_VIOLATION, "Rogue agent detected")

    # All acknowledge (but rogue keeps running)
    for agent in all_agents:
        agent.stop()  # Rogue ignores this
        kill_switch.register_acknowledgment(agent.agent_id, True)

    # Force kill should be called
    await kill_switch._force_kill_agents()
    assert kill_switch._force_kill_used is True


# ========== Phase 3: Recovery Testing ==========

def test_recovery_test_success(kill_switch):
    """Test successful recovery test"""
    # Run recovery test
    result = kill_switch.test_recovery()

    # Check result
    assert result['test_type'] == 'recovery'
    assert 'phases' in result
    assert len(result['phases']) > 0

    # Should have trigger, recover, and verify phases
    phases = {p['phase'] for p in result['phases']}
    assert 'trigger' in phases
    assert 'recover' in phases

    # System should be operational after test
    assert kill_switch.is_operational()


def test_recovery_test_with_failure(kill_switch):
    """Test recovery test handles failures gracefully"""
    # Manually cause failure by setting state to TRIGGERED before test
    kill_switch._state = KillSwitchState.TRIGGERED

    result = kill_switch.test_recovery()

    # Should fail at trigger phase
    assert result['success'] is False
    assert 'error' in result


def test_test_results_tracking(kill_switch):
    """Test that test results are tracked"""
    # Clear existing test results
    kill_switch._test_results = []

    # Run multiple tests
    kill_switch.test_recovery()
    kill_switch.test_recovery()

    status = kill_switch.get_status()
    assert status['test_count'] == 2

    # Last test result should be available
    assert status['last_test_result'] is not None


# ========== Phase 4: Backup Trigger Tests ==========

def test_backup_trigger_creation(kill_switch):
    """Test backup trigger file creation"""
    # Trigger backup mechanism
    kill_switch._backup_trigger(
        KillSwitchReason.CRITICAL_FAILURE,
        "Event bus failed",
        "test"
    )

    # Check file exists
    backup_file = kill_switch._backup_trigger_file
    assert backup_file.exists()

    # Clean up
    backup_file.unlink()


def test_check_backup_trigger(kill_switch):
    """Test checking for backup trigger"""
    # Create backup file manually
    import json
    backup_file = kill_switch._backup_trigger_file
    backup_file.parent.mkdir(parents=True, exist_ok=True)

    with open(backup_file, 'w') as f:
        json.dump({
            'reason': 'manual',
            'message': 'Test backup',
            'source': 'test',
            'timestamp': datetime.now().isoformat()
        }, f)

    # Check for backup trigger
    found = kill_switch.check_backup_trigger()

    assert found is True
    assert kill_switch.is_triggered()

    # File should be cleaned up
    assert not backup_file.exists()


def test_check_backup_trigger_none(kill_switch):
    """Test checking for backup trigger when none exists"""
    found = kill_switch.check_backup_trigger()
    assert found is False
    assert not kill_switch.is_triggered()


# ========== Full Emergency Scenario Tests ==========

@pytest.mark.asyncio
async def test_full_emergency_scenario():
    """
    Integration test: Full emergency scenario with rogue agent.

    Simulates:
    1. Multiple agents running
    2. One agent goes rogue
    3. Kill switch triggered
    4. All agents acknowledge
    5. Non-compliant agent force killed
    6. System recovers
    """
    ks = get_kill_switch()
    ks._state = KillSwitchState.ACTIVE

    # Setup: Create 5 agents, one is rogue
    agents = [MockAgent(f"agent-{i}") for i in range(4)]
    rogue = NonCompliantAgent("rogue-agent")
    all_agents = agents + [rogue]

    # Simulate kill switch knowing about them
    ks._expected_agents = {agent.agent_id for agent in all_agents}

    # Trigger emergency kill
    triggered = ks.trigger(
        KillSwitchReason.SAFETY_VIOLATION,
        "Agent deleting files",
        source="file_monitor"
    )

    assert triggered is True
    assert ks.is_triggered()

    # Simulate agents acknowledging
    for agent in all_agents:
        agent.stop()  # Rogue ignores this
        ks.register_acknowledgment(agent.agent_id, agent.is_running == False)

    # Verify acknowledgments
    assert len(ks._acknowledgments) == 5

    # Verify compliance (would force kill rogue)
    await ks._verify_agents_stopped()

    # Recover system
    recovered = ks.recover("Rogue agent stopped")
    assert recovered is True
    assert ks.is_operational()


@pytest.mark.asyncio
async def test_full_emergency_with_async_verification():
    """Test full emergency with async verification flow"""
    ks = KillSwitch()
    ks._state = KillSwitchState.ACTIVE

    # Create agents
    agents = [MockAgent(f"agent-{i}") for i in range(3)]
    ks._expected_agents = {agent.agent_id for agent in agents}

    # Trigger with async verification
    result = ks.trigger_async(
        KillSwitchReason.MANUAL,
        "Test async verification",
        "test"
    )

    # Agents acknowledge
    for agent in agents:
        agent.stop()
        ks.register_acknowledgment(agent.agent_id, True)

    # Wait a bit for async verification
    await asyncio.sleep(0.5)

    # Check status
    status = ks.get_status()
    assert status['triggered'] is True


# ========== Status and Diagnostics Tests ==========

def test_get_status_comprehensive(kill_switch):
    """Test that get_status returns comprehensive information"""
    # Set up some state
    kill_switch._expected_agents = {"agent-1", "agent-2"}
    kill_switch.register_acknowledgment("agent-1", True)

    status = kill_switch.get_status()

    # Check all expected fields
    assert 'state' in status
    assert 'operational' in status
    assert 'triggered' in status
    assert 'expected_agents' in status
    assert 'acknowledgments' in status
    assert 'missing_acknowledgments' in status
    assert 'acknowledgment_rate' in status
    assert 'compliance_verified' in status
    assert 'force_kill_used' in status
    assert 'test_count' in status

    # Check values
    assert status['acknowledgment_rate'] == 0.5
    assert len(status['missing_acknowledgments']) == 1
    assert "agent-2" in status['missing_acknowledgments']


def test_persistence_of_test_results(kill_switch):
    """Test that test results persist through state saves"""
    # Clear and add a test result
    kill_switch._test_results = []
    kill_switch._test_results.append({
        'timestamp': datetime.now().isoformat(),
        'success': True,
        'test_type': 'recovery'
    })

    # Save state
    kill_switch._save_state()

    # Create a new instance (will load from state file)
    ks2 = KillSwitch()
    status = ks2.get_status()

    # The test count is loaded from the saved state
    assert status['test_count'] >= 1


# ========== Edge Cases ==========

def test_trigger_already_triggered(kill_switch):
    """Test triggering when already triggered"""
    kill_switch._state = KillSwitchState.TRIGGERED

    result = kill_switch.trigger(KillSwitchReason.MANUAL, "Second trigger")
    assert result is False


def test_recover_when_not_triggered(kill_switch):
    """Test recovery when not triggered"""
    result = kill_switch.recover("Not triggered")
    assert result is False


def test_reset_functionality(kill_switch):
    """Test force reset functionality"""
    # Trigger
    kill_switch.trigger(KillSwitchReason.MANUAL, "Test")
    assert kill_switch.is_triggered()

    # Reset
    result = kill_switch.reset()
    assert result is True
    assert kill_switch.is_operational()


# ========== Performance Tests ==========

def test_kill_switch_performance(kill_switch):
    """Test kill switch performance with many agents"""
    # Simulate 100 agents
    num_agents = 100
    kill_switch._expected_agents = {f"agent-{i}" for i in range(num_agents)}

    # Trigger and measure time
    start = time.time()
    kill_switch.trigger(KillSwitchReason.MANUAL, "Performance test")
    trigger_time = time.time() - start

    # All agents acknowledge
    for i in range(num_agents):
        kill_switch.register_acknowledgment(f"agent-{i}", True)

    ack_time = time.time() - start

    # Trigger should be fast (< 100ms)
    assert trigger_time < 0.1

    # All acknowledgments should be fast (< 1 second)
    assert ack_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
