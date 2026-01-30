"""
Tests for Orchestrator Checkpointing and Resume Capability
===========================================================

Tests the AgentOrchestrator's ability to:
- Save checkpoints after each completed step
- Resume workflows from checkpoints
- Skip completed steps when resuming
- Detect circular dependencies (deadlocks)
- Clean up checkpoints after completion
"""

import asyncio
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "01-core"))

from orchestration.Orchestrator import (
    AgentOrchestrator,
    Workflow,
    WorkflowStep,
    WorkflowStatus,
)
from agents.core.base_agent import BaseAgent, AgentConfig, AgentTask, AgentResult


# =============================================================================
# MOCK AGENT FOR TESTING
# =============================================================================

class MockAgent(BaseAgent):
    """A mock agent for testing orchestration."""

    def __init__(self, name: str = "test_agent"):
        config = AgentConfig(
            name=name,
            full_name=f"Test Agent {name}",
            role="tester",
            category="testing",
            description="A test agent",
        )
        super().__init__(config)
        self.execute_call_count = 0
        self.execute_delay = 0.1  # Small delay for testing

    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute task with optional delay."""
        self.execute_call_count += 1
        await asyncio.sleep(self.execute_delay)

        return AgentResult(
            success=True,
            output=f"Executed task {task.id}",
            metadata={"agent": self.name, "call_count": self.execute_call_count}
        )

    async def think(self, task: AgentTask) -> list:
        """Return thinking steps."""
        return [
            f"Understanding task: {task.description}",
            "Processing task",
            "Returning result",
        ]


class FailingAgent(BaseAgent):
    """An agent that fails on specific steps."""

    def __init__(self, name: str = "failing_agent", fail_on_steps: list = None):
        config = AgentConfig(
            name=name,
            full_name=f"Failing Agent {name}",
            role="tester",
            category="testing",
            description="A test agent that fails",
        )
        super().__init__(config)
        self.fail_on_steps = fail_on_steps or []
        self.execute_call_count = 0

    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute task, failing on configured steps."""
        self.execute_call_count += 1

        if task.id in self.fail_on_steps:
            raise Exception(f"Simulated failure for task {task.id}")

        return AgentResult(
            success=True,
            output=f"Executed task {task.id}",
        )

    async def think(self, task: AgentTask) -> list:
        return ["Thinking about task"]


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_checkpoint_dir():
    """Create a temporary directory for checkpoints."""
    temp_dir = tempfile.mkdtemp(prefix="bb5_checkpoints_")
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    event_bus = Mock()
    event_bus.publish = AsyncMock()
    return event_bus


@pytest.fixture
def orchestrator_with_checkpoints(temp_checkpoint_dir, mock_event_bus):
    """Create an orchestrator with checkpointing enabled."""
    orchestrator = AgentOrchestrator(
        event_bus=mock_event_bus,
        task_router=None,
        memory_base_path=temp_checkpoint_dir,
        max_concurrent_agents=5,
        enable_checkpoints=True,
    )
    return orchestrator


@pytest.fixture
def orchestrator_without_checkpoints(temp_checkpoint_dir, mock_event_bus):
    """Create an orchestrator with checkpointing disabled."""
    orchestrator = AgentOrchestrator(
        event_bus=mock_event_bus,
        task_router=None,
        memory_base_path=temp_checkpoint_dir,
        max_concurrent_agents=5,
        enable_checkpoints=False,
    )
    return orchestrator


@pytest.fixture
def registered_agents(orchestrator_with_checkpoints):
    """Register mock agents with the orchestrator."""
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    agent3 = MockAgent("agent3")

    asyncio.run(orchestrator_with_checkpoints.register_agent(agent1))
    asyncio.run(orchestrator_with_checkpoints.register_agent(agent2))
    asyncio.run(orchestrator_with_checkpoints.register_agent(agent3))

    return {
        "agent1": agent1,
        "agent2": agent2,
        "agent3": agent3,
    }


# =============================================================================
# CHECKPOINT CREATION TESTS
# =============================================================================

class TestCheckpointCreation:
    """Tests for checkpoint file creation and content."""

    @pytest.mark.asyncio
    async def test_checkpoint_created_after_each_step(
        self, orchestrator_with_checkpoints, registered_agents
    ):
        """Test that checkpoint is created after each completed step."""
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="agent2",
                    task=AgentTask(id="task2", description="Task 2"),
                ),
            ],
        )

        # Execute workflow
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)

        # Verify workflow completed
        assert result.status == WorkflowStatus.COMPLETED

        # Check checkpoint directory exists
        assert orchestrator_with_checkpoints._checkpoint_dir.exists()

        # Note: Checkpoint should be deleted after completion
        checkpoint_file = orchestrator_with_checkpoints._checkpoint_dir / f"{workflow.id}.json"
        assert not checkpoint_file.exists(), "Checkpoint should be cleaned up after completion"

    @pytest.mark.asyncio
    async def test_checkpoint_contains_correct_data(
        self, orchestrator_with_checkpoints, registered_agents, temp_checkpoint_dir
    ):
        """Test that checkpoint file contains correct workflow data."""
        workflow = Workflow(
            id="test-workflow-1",
            name="Test Workflow",
            description="A test workflow",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="agent2",
                    task=AgentTask(id="task2", description="Task 2"),
                    depends_on=["step1"],
                ),
            ],
        )

        # Manually create a checkpoint to test its structure
        from orchestration.Orchestrator import AgentOrchestrator
        orchestrator_with_checkpoints._save_checkpoint(workflow, {"step1"})

        checkpoint_file = temp_checkpoint_dir / "checkpoints" / f"{workflow.id}.json"
        assert checkpoint_file.exists()

        # Load and verify checkpoint data
        data = json.loads(checkpoint_file.read_text())
        assert data['workflow_id'] == workflow.id
        assert data['workflow_name'] == workflow.name
        assert 'step1' in data['completed_steps']
        assert len(data['steps']) == 2

        # Verify step data
        step1_data = next(s for s in data['steps'] if s['id'] == 'step1')
        assert step1_data['name'] == "Step 1"

    @pytest.mark.asyncio
    async def test_checkpoint_disabled_when_flag_false(
        self, orchestrator_without_checkpoints, registered_agents
    ):
        """Test that no checkpoints are created when disabled."""
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
            ],
        )

        await orchestrator_without_checkpoints.execute_workflow(workflow)

        # Verify no checkpoint directory was created
        assert orchestrator_without_checkpoints._checkpoint_dir is None


# =============================================================================
# RESUME FROM CHECKPOINT TESTS
# =============================================================================

class TestResumeFromCheckpoint:
    """Tests for resuming workflows from checkpoints."""

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint_skips_completed_steps(
        self, orchestrator_with_checkpoints, registered_agents, temp_checkpoint_dir
    ):
        """Test that resuming skips already completed steps."""
        workflow = Workflow(
            id="resume-test-1",
            name="Resume Test Workflow",
            description="Testing resume",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="agent2",
                    task=AgentTask(id="task2", description="Task 2"),
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    agent_name="agent3",
                    task=AgentTask(id="task3", description="Task 3"),
                    depends_on=["step2"],
                ),
            ],
        )

        # Create a checkpoint indicating step1 is complete
        checkpoint_data = {
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'completed_steps': ['step1'],
            'steps': [
                {
                    'id': 'step1',
                    'name': 'Step 1',
                    'status': 'completed',
                    'retry_count': 0,
                    'error': None,
                    'started_at': datetime.now().isoformat(),
                    'completed_at': datetime.now().isoformat(),
                },
                {
                    'id': 'step2',
                    'name': 'Step 2',
                    'status': 'pending',
                    'retry_count': 0,
                    'error': None,
                    'started_at': None,
                    'completed_at': None,
                },
                {
                    'id': 'step3',
                    'name': 'Step 3',
                    'status': 'pending',
                    'retry_count': 0,
                    'error': None,
                    'started_at': None,
                    'completed_at': None,
                },
            ],
            'timestamp': datetime.now().isoformat()
        }

        checkpoint_file = temp_checkpoint_dir / "checkpoints" / f"{workflow.id}.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text(json.dumps(checkpoint_data))

        # Reset agent call counts
        for agent in registered_agents.values():
            agent.execute_call_count = 0

        # Execute workflow - should resume from checkpoint
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)

        # Verify workflow completed
        assert result.status == WorkflowStatus.COMPLETED

        # Verify agent1 was NOT called again (step was already complete)
        assert registered_agents["agent1"].execute_call_count == 0

        # Verify agent2 and agent3 were called
        assert registered_agents["agent2"].execute_call_count == 1
        assert registered_agents["agent3"].execute_call_count == 1

    @pytest.mark.asyncio
    async def test_no_checkpoint_starts_from_beginning(
        self, orchestrator_with_checkpoints, registered_agents
    ):
        """Test that workflow starts from beginning when no checkpoint exists."""
        workflow = Workflow(
            id="no-checkpoint-test",
            name="No Checkpoint Test",
            description="Testing without checkpoint",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="agent2",
                    task=AgentTask(id="task2", description="Task 2"),
                    depends_on=["step1"],
                ),
            ],
        )

        # Reset call counts
        for agent in registered_agents.values():
            agent.execute_call_count = 0

        # Execute workflow
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)

        # Verify all steps were executed
        assert result.status == WorkflowStatus.COMPLETED
        assert registered_agents["agent1"].execute_call_count == 1
        assert registered_agents["agent2"].execute_call_count == 1

    @pytest.mark.asyncio
    async def test_resume_with_partial_completion(
        self, orchestrator_with_checkpoints, registered_agents, temp_checkpoint_dir
    ):
        """Test resuming workflow with some steps completed and some failed."""
        workflow = Workflow(
            id="partial-resume-test",
            name="Partial Resume Test",
            description="Testing partial resume",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="agent2",
                    task=AgentTask(id="task2", description="Task 2"),
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    agent_name="agent3",
                    task=AgentTask(id="task3", description="Task 3"),
                    depends_on=["step2"],
                ),
            ],
        )

        # Create checkpoint with step1 complete, step2 failed (pending retry)
        checkpoint_data = {
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'completed_steps': ['step1'],
            'steps': [
                {
                    'id': 'step1',
                    'name': 'Step 1',
                    'status': 'completed',
                    'retry_count': 0,
                    'error': None,
                },
                {
                    'id': 'step2',
                    'name': 'Step 2',
                    'status': 'pending',
                    'retry_count': 1,
                    'error': 'Previous error',
                },
                {
                    'id': 'step3',
                    'name': 'Step 3',
                    'status': 'pending',
                    'retry_count': 0,
                    'error': None,
                },
            ],
            'timestamp': datetime.now().isoformat()
        }

        checkpoint_file = temp_checkpoint_dir / "checkpoints" / f"{workflow.id}.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text(json.dumps(checkpoint_data))

        # Reset call counts
        for agent in registered_agents.values():
            agent.execute_call_count = 0

        # Execute workflow - should resume
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)

        # Verify completion
        assert result.status == WorkflowStatus.COMPLETED

        # Verify step2 state was restored (retry_count preserved)
        step2 = next(s for s in workflow.steps if s.id == "step2")
        assert step2.retry_count == 1  # Should preserve retry count

    @pytest.mark.asyncio
    async def test_checkpoint_cleaned_after_completion(
        self, orchestrator_with_checkpoints, registered_agents, temp_checkpoint_dir
    ):
        """Test that checkpoint is deleted after workflow completes."""
        workflow = Workflow(
            id="cleanup-test",
            name="Cleanup Test",
            description="Testing checkpoint cleanup",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
            ],
        )

        # Create initial checkpoint
        checkpoint_data = {
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'completed_steps': [],
            'steps': [],
            'timestamp': datetime.now().isoformat()
        }

        checkpoint_file = temp_checkpoint_dir / "checkpoints" / f"{workflow.id}.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text(json.dumps(checkpoint_data))

        # Verify checkpoint exists
        assert checkpoint_file.exists()

        # Execute workflow to completion
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)

        # Verify checkpoint was cleaned up
        assert result.status == WorkflowStatus.COMPLETED
        assert not checkpoint_file.exists(), "Checkpoint should be deleted after completion"

    @pytest.mark.asyncio
    async def test_checkpoint_cleaned_after_failure(
        self, orchestrator_with_checkpoints, temp_checkpoint_dir
    ):
        """Test that checkpoint is deleted after workflow fails."""
        # Register failing agent
        failing_agent = FailingAgent("failing_agent", fail_on_steps=["task2"])
        await orchestrator_with_checkpoints.register_agent(failing_agent)

        workflow = Workflow(
            id="failure-cleanup-test",
            name="Failure Cleanup Test",
            description="Testing checkpoint cleanup on failure",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="failing_agent",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="failing_agent",
                    task=AgentTask(id="task2", description="Task 2"),
                    depends_on=["step1"],
                ),
            ],
        )

        # Create initial checkpoint
        checkpoint_data = {
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'completed_steps': ['step1'],
            'steps': [],
            'timestamp': datetime.now().isoformat()
        }

        checkpoint_file = temp_checkpoint_dir / "checkpoints" / f"{workflow.id}.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text(json.dumps(checkpoint_data))

        # Execute workflow - will fail
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)

        # Verify checkpoint was cleaned up even on failure
        assert result.status == WorkflowStatus.FAILED
        assert not checkpoint_file.exists(), "Checkpoint should be deleted after failure"


# =============================================================================
# DEADLOCK DETECTION TESTS
# =============================================================================

class TestDeadlockDetection:
    """Tests for circular dependency detection."""

    @pytest.mark.asyncio
    async def test_detect_circular_dependency(
        self, orchestrator_with_checkpoints, registered_agents, caplog
    ):
        """Test that circular dependencies are detected and workflow fails."""
        import logging
        caplog.set_level(logging.ERROR)

        workflow = Workflow(
            name="Circular Workflow",
            description="Testing circular dependency detection",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                    depends_on=["step2"],  # Circular!
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="agent2",
                    task=AgentTask(id="task2", description="Task 2"),
                    depends_on=["step1"],  # Circular!
                ),
            ],
        )

        # Should detect deadlock and return failed workflow
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)

        # Verify workflow failed due to deadlock
        assert result.status == WorkflowStatus.FAILED

        # Verify the error was logged with deadlock information
        assert any("deadlock" in record.message.lower() for record in caplog.records)
        assert any("circular" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_detect_complex_circular_dependency(
        self, orchestrator_with_checkpoints, registered_agents, caplog
    ):
        """Test detection of complex circular dependencies (A->B->C->A)."""
        import logging
        caplog.set_level(logging.ERROR)

        workflow = Workflow(
            name="Complex Circular Workflow",
            description="Testing complex circular dependency",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                    depends_on=["step3"],
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="agent2",
                    task=AgentTask(id="task2", description="Task 2"),
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    agent_name="agent3",
                    task=AgentTask(id="task3", description="Task 3"),
                    depends_on=["step2"],
                ),
            ],
        )

        # Should detect deadlock and return failed workflow
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)

        # Verify workflow failed due to deadlock
        assert result.status == WorkflowStatus.FAILED

        # Verify the error was logged with deadlock information
        assert any("deadlock" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_no_deadlock_with_valid_dependencies(
        self, orchestrator_with_checkpoints, registered_agents
    ):
        """Test that valid workflows don't trigger deadlock detection."""
        workflow = Workflow(
            name="Valid Sequential Workflow",
            description="Testing valid sequential workflow",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="agent2",
                    task=AgentTask(id="task2", description="Task 2"),
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    agent_name="agent3",
                    task=AgentTask(id="task3", description="Task 3"),
                    depends_on=["step2"],
                ),
            ],
        )

        # Should complete successfully
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)
        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_deadlock_detection_with_parallel_steps(
        self, orchestrator_with_checkpoints, registered_agents
    ):
        """Test deadlock detection with mix of parallel and sequential steps."""
        workflow = Workflow(
            name="Mixed Workflow",
            description="Testing mixed parallel/sequential",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2a",
                    name="Step 2a",
                    agent_name="agent2",
                    task=AgentTask(id="task2a", description="Task 2a"),
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step2b",
                    name="Step 2b",
                    agent_name="agent3",
                    task=AgentTask(id="task2b", description="Task 2b"),
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    agent_name="agent1",
                    task=AgentTask(id="task3", description="Task 3"),
                    depends_on=["step2a", "step2b"],
                ),
            ],
        )

        # Should complete successfully (no circular dependency)
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)
        assert result.status == WorkflowStatus.COMPLETED

    def test_detect_circular_dependencies_algorithm(self):
        """Test the circular dependency detection algorithm directly."""
        orchestrator = AgentOrchestrator(enable_checkpoints=True)

        # Test 1: Simple circular dependency
        graph1 = {
            "A": ["B"],
            "B": ["A"],
        }
        cycles1 = orchestrator._detect_circular_dependencies(graph1)
        assert len(cycles1) > 0
        assert any("A" in cycle and "B" in cycle for cycle in cycles1)

        # Test 2: Complex circular dependency
        graph2 = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],
        }
        cycles2 = orchestrator._detect_circular_dependencies(graph2)
        assert len(cycles2) > 0

        # Test 3: No circular dependency
        graph3 = {
            "A": [],
            "B": ["A"],
            "C": ["B"],
        }
        cycles3 = orchestrator._detect_circular_dependencies(graph3)
        assert len(cycles3) == 0

        # Test 4: Multiple independent cycles
        graph4 = {
            "A": ["B"],
            "B": ["A"],
            "C": ["D"],
            "D": ["C"],
        }
        cycles4 = orchestrator._detect_circular_dependencies(graph4)
        assert len(cycles4) >= 2

    def test_build_dependency_graph(self):
        """Test dependency graph building for debugging."""
        orchestrator = AgentOrchestrator(enable_checkpoints=True)

        workflow = Workflow(
            name="Test",
            description="Test",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="agent2",
                    task=AgentTask(id="task2", description="Task 2"),
                    depends_on=["step1"],
                ),
            ],
        )

        completed = set()
        graph = orchestrator._build_dependency_graph(workflow, completed)

        # Should have blocked steps
        assert len(graph['blocked']) == 1
        assert graph['blocked'][0]['step'] == 'step2'
        assert 'step1' in graph['blocked'][0]['waiting_for']

        # No circular dependencies
        assert len(graph['circular']) == 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestCheckpointIntegration:
    """Integration tests for checkpoint functionality."""

    @pytest.mark.asyncio
    async def test_crash_and_resume_scenario(
        self, orchestrator_with_checkpoints, registered_agents, temp_checkpoint_dir
    ):
        """Simulate a crash during workflow execution and resume."""
        workflow = Workflow(
            id="crash-test",
            name="Crash Test Workflow",
            description="Testing crash recovery",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    agent_name="agent2",
                    task=AgentTask(id="task2", description="Task 2"),
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    agent_name="agent3",
                    task=AgentTask(id="task3", description="Task 3"),
                    depends_on=["step2"],
                ),
                WorkflowStep(
                    id="step4",
                    name="Step 4",
                    agent_name="agent1",
                    task=AgentTask(id="task4", description="Task 4"),
                    depends_on=["step3"],
                ),
            ],
        )

        # Simulate crash after step 2 completes by creating checkpoint
        checkpoint_data = {
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'completed_steps': ['step1', 'step2'],
            'steps': [
                {
                    'id': 'step1',
                    'name': 'Step 1',
                    'status': 'completed',
                    'retry_count': 0,
                    'error': None,
                    'started_at': datetime.now().isoformat(),
                    'completed_at': datetime.now().isoformat(),
                },
                {
                    'id': 'step2',
                    'name': 'Step 2',
                    'status': 'completed',
                    'retry_count': 0,
                    'error': None,
                    'started_at': datetime.now().isoformat(),
                    'completed_at': datetime.now().isoformat(),
                },
                {
                    'id': 'step3',
                    'name': 'Step 3',
                    'status': 'pending',
                    'retry_count': 0,
                    'error': None,
                },
                {
                    'id': 'step4',
                    'name': 'Step 4',
                    'status': 'pending',
                    'retry_count': 0,
                    'error': None,
                },
            ],
            'timestamp': datetime.now().isoformat()
        }

        checkpoint_file = temp_checkpoint_dir / "checkpoints" / f"{workflow.id}.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text(json.dumps(checkpoint_data))

        # Reset agent call counts
        for agent in registered_agents.values():
            agent.execute_call_count = 0

        # "Resume" workflow
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)

        # Verify workflow completed
        assert result.status == WorkflowStatus.COMPLETED

        # Verify steps 1 and 2 were NOT re-executed
        assert registered_agents["agent1"].execute_call_count == 1  # Only step4
        assert registered_agents["agent2"].execute_call_count == 0  # Step2 was done
        assert registered_agents["agent3"].execute_call_count == 1  # Step3

    @pytest.mark.asyncio
    async def test_parallel_workflow_with_checkpoint(
        self, orchestrator_with_checkpoints, registered_agents, temp_checkpoint_dir
    ):
        """Test checkpoint behavior with parallel workflows."""
        workflow = Workflow(
            id="parallel-test",
            name="Parallel Workflow",
            description="Testing parallel execution with checkpoints",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    agent_name="agent1",
                    task=AgentTask(id="task1", description="Task 1"),
                ),
                WorkflowStep(
                    id="step2a",
                    name="Step 2a",
                    agent_name="agent2",
                    task=AgentTask(id="task2a", description="Task 2a"),
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step2b",
                    name="Step 2b",
                    agent_name="agent3",
                    task=AgentTask(id="task2b", description="Task 2b"),
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    agent_name="agent1",
                    task=AgentTask(id="task3", description="Task 3"),
                    depends_on=["step2a", "step2b"],
                ),
            ],
        )

        # Simulate crash after step 2a completes (but 2b is still pending)
        checkpoint_data = {
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'completed_steps': ['step1', 'step2a'],
            'steps': [],
            'timestamp': datetime.now().isoformat()
        }

        checkpoint_file = temp_checkpoint_dir / "checkpoints" / f"{workflow.id}.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text(json.dumps(checkpoint_data))

        # Reset call counts
        for agent in registered_agents.values():
            agent.execute_call_count = 0

        # Resume workflow
        result = await orchestrator_with_checkpoints.execute_workflow(workflow)

        # Verify completion
        assert result.status == WorkflowStatus.COMPLETED

        # Verify step1 and step2a were not re-executed
        assert registered_agents["agent2"].execute_call_count == 0  # step2a was done

        # Verify step2b and step3 were executed
        assert registered_agents["agent3"].execute_call_count == 1  # step2b
        assert registered_agents["agent1"].execute_call_count == 1  # step3


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x"])
