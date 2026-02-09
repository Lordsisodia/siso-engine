"""
Pytest Configuration and Fixtures
==================================

Shared fixtures and configuration for RALF test suite.
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path
import pytest

# Add lib directory to path for test utilities
sys.path.insert(0, str(Path(__file__).parent / "lib"))


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test files.

    Yields:
        Path: Temporary directory path (auto-cleaned)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config():
    """
    Sample valid configuration for testing.

    Returns:
        dict: Sample configuration
    """
    return {
        "thresholds": {
            "skill_invocation_confidence": 70,
            "queue_depth_min": 3,
            "queue_depth_max": 5,
        },
        "routing": {
            "default_agent": "executor",
            "task_type_routing": {
                "implementation": "executor",
                "planning": "planner",
            }
        },
        "notifications": {
            "enabled": False,
            "level": "INFO",
        }
    }


@pytest.fixture
def sample_task():
    """
    Sample task for testing.

    Returns:
        dict: Sample task
    """
    return {
        "task_id": "TASK-001",
        "type": "implement",
        "priority": "high",
        "status": "pending",
        "title": "Sample Task",
        "objective": "Test objective",
        "approach": "Test approach"
    }


@pytest.fixture
def sample_event():
    """
    Sample event for testing.

    Returns:
        dict: Sample event
    """
    return {
        "timestamp": "2026-02-01T12:00:00Z",
        "task_id": "TASK-001",
        "type": "started",
        "agent": "executor",
        "run_number": 1,
        "result": "success"
    }


@pytest.fixture
def mock_yaml_file(temp_dir, sample_config):
    """
    Create a mock YAML file with sample config.

    Args:
        temp_dir: Temporary directory fixture
        sample_config: Sample config fixture

    Returns:
        Path: Path to mock YAML file
    """
    yaml_file = temp_dir / "test_config.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(sample_config, f)
    return yaml_file


@pytest.fixture
def engine_lib_path():
    """
    Path to engine lib directory for imports.

    Returns:
        Path: Engine lib directory
    """
    return Path("/workspaces/blackbox5/2-engine/.autonomous/lib")


@pytest.fixture(autouse=True)
def reset_environment():
    """
    Reset environment variables before each test.
    """
    # Save original environment
    original_env = os.environ.copy()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
