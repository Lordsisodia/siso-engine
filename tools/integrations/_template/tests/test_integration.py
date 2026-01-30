"""
Tests for {SERVICE_NAME} integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from integration.{SERVICE_LOWER} import {ServiceName}Manager
from integration.{SERVICE_LOWER}.types import EntityType, EntityStatus


@pytest.fixture
def mock_manager():
    """Create a mock manager."""
    manager = {ServiceName}Manager(token="test_token")
    manager.client = AsyncMock()
    return manager


@pytest.mark.asyncio
async def test_check_connection(mock_manager):
    """Test connection check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_manager.client.get.return_value = mock_response

    result = await mock_manager.check_connection()
    assert result is True


@pytest.mark.asyncio
async def test_some_operation(mock_manager):
    """Test basic operation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "123", "name": "test"}
    mock_manager.client.get.return_value = mock_response

    result = await mock_manager.some_operation(param1="value")
    assert result["id"] == "123"


@pytest.mark.asyncio
async def test_create_entity(mock_manager):
    """Test entity creation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "123",
        "name": "Test Entity",
        "status": "active",
        "created_at": "2025-01-19T00:00:00Z",
        "metadata": {},
    }
    mock_manager.client.post.return_value = mock_response

    from integration.{SERVICE_LOWER}.types import OperationSpec
    spec = OperationSpec(param1="test")

    entity = await mock_manager.create_entity(spec)
    assert entity.id == "123"
    assert entity.name == "Test Entity"
