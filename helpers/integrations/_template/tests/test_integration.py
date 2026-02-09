"""
Tests for SERVICE_NAME integration.

TODO: Replace SERVICE_NAME with actual service name.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

# TODO: Update imports when implementing actual integration
# from integration.service_name import TemplateManager
# from integration.service_name.types import EntityType, EntityStatus

from manager import TemplateManager


@pytest.fixture
def mock_manager():
    """Create a mock manager."""
    manager = TemplateManager(token="test_token")
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

    from manager import OperationSpec
    spec = OperationSpec(param1="test")

    entity = await mock_manager.create_entity(spec)
    assert entity.id == "123"
    assert entity.name == "Test Entity"
