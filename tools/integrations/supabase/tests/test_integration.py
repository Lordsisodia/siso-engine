#!/usr/bin/env python3
"""
Supabase Integration Tests
===========================

Unit tests for Supabase integration manager.

Usage:
    pytest test_integration.py -v
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from integration.supabase import SupabaseManager
from integration.supabase.config import SupabaseConfig
from integration.supabase.types import InsertResult


@pytest.fixture
def config():
    """Get test config."""
    return SupabaseConfig(
        project_ref="test-ref",
        service_role_key="test-key",
    )


@pytest_asyncio.fixture
async def manager(config):
    """Get test manager."""
    async with SupabaseManager(config) as m:
        yield m


@pytest.mark.asyncio
class TestSupabaseManager:
    """Test SupabaseManager class."""

    async def test_init_with_config(self, config):
        """Test initialization with config."""
        manager = SupabaseManager(config)
        assert manager.config == config
        assert manager.api_url == config.api_url
        await manager.close()

    async def test_init_with_params(self):
        """Test initialization with parameters."""
        manager = SupabaseManager(
            project_ref="test-ref",
            service_role_key="test-key",
        )
        assert manager.config.project_ref == "test-ref"
        assert manager.config.service_role_key == "test-key"
        await manager.close()

    async def test_init_missing_credentials(self):
        """Test initialization fails without credentials."""
        with pytest.raises(ValueError, match="project_ref required"):
            SupabaseManager(project_ref=None, service_role_key="key")

        with pytest.raises(ValueError, match="service_role_key required"):
            SupabaseManager(project_ref="ref", service_role_key=None)

    async def test_check_connection_success(self, manager):
        """Test successful connection check."""
        with patch.object(manager.client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = await manager.check_connection()
            assert result is True

    async def test_check_connection_failure(self, manager):
        """Test failed connection check."""
        with patch.object(manager.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection error")

            result = await manager.check_connection()
            assert result is False

    async def test_query_basic(self, manager):
        """Test basic query operation."""
        with patch.object(manager.client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": 1, "name": "Test"},
                {"id": 2, "name": "Test 2"},
            ]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = await manager.query("test_table")
            assert len(result) == 2
            assert result[0]["name"] == "Test"

    async def test_query_with_filters(self, manager):
        """Test query with filters."""
        with patch.object(manager.client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [{"id": 1, "status": "active"}]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = await manager.query(
                "test_table",
                filters={"status": "active"},
                limit=10,
            )

            assert len(result) == 1
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert "params" in call_kwargs
            assert call_kwargs["params"]["limit"] == 10

    async def test_insert_single(self, manager):
        """Test insert single record."""
        with patch.object(manager.client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": 1, "name": "Test", "created_at": "2024-01-01"}
            ]
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            result = await manager.insert("test_table", {"name": "Test"})

            assert isinstance(result, InsertResult)
            assert len(result.data) == 1
            assert result.data[0]["name"] == "Test"

    async def test_insert_bulk(self, manager):
        """Test bulk insert."""
        with patch.object(manager.client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": 1, "name": "Test 1"},
                {"id": 2, "name": "Test 2"},
            ]
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            result = await manager.insert(
                "test_table",
                [{"name": "Test 1"}, {"name": "Test 2"}],
            )

            assert len(result.data) == 2

    async def test_update(self, manager):
        """Test update operation."""
        with patch.object(manager.client, "patch", new_callable=AsyncMock) as mock_patch:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": 1, "status": "updated"}
            ]
            mock_response.raise_for_status = MagicMock()
            mock_patch.return_value = mock_response

            result = await manager.update(
                "test_table",
                data={"status": "updated"},
                filters={"id": 1},
            )

            assert len(result.data) == 1
            assert result.data[0]["status"] == "updated"

    async def test_delete(self, manager):
        """Test delete operation."""
        with patch.object(manager.client, "delete", new_callable=AsyncMock) as mock_delete:
            mock_response = MagicMock()
            mock_response.headers = {"content-range": "*/1"}
            mock_response.raise_for_status = MagicMock()
            mock_delete.return_value = mock_response

            result = await manager.delete(
                "test_table",
                filters={"id": 1},
            )

            assert result.count == 1

    async def test_upload_file(self, manager):
        """Test file upload."""
        with patch("httpx.AsyncClient", new_callable=AsyncMock) as mock_client:
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"Key": "test/file.txt"}
            mock_response.raise_for_status = MagicMock()
            mock_instance.put = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await manager.upload_file(
                bucket="test-bucket",
                path="test/file.txt",
                content=b"test content",
            )

            assert result["Key"] == "test/file.txt"

    async def test_get_public_url(self, manager):
        """Test getting public URL."""
        url = await manager.get_public_url("bucket", "path/file.txt")
        assert "bucket" in url
        assert "path/file.txt" in url
        assert url.startswith("https://")

    async def test_invoke_function(self, manager):
        """Test Edge Function invocation."""
        with patch.object(manager.client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": "success"}
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.is_error = False
            mock_post.return_value = mock_response

            result = await manager.invoke_function(
                name="test-function",
                body={"param": "value"},
            )

            assert result.data["result"] == "success"
            assert result.status_code == 200

    async def test_count(self, manager):
        """Test count operation."""
        with patch.object(manager.client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.headers = {"content-range": "0-9/100"}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            count = await manager.count("test_table")

            assert count == 100


@pytest.mark.asyncio
class TestSupabaseConfig:
    """Test SupabaseConfig class."""

    def test_from_env(self):
        """Test loading config from environment."""
        with patch.dict(os.environ, {
            "SUPABASE_PROJECT_REF": "test-ref",
            "SUPABASE_SERVICE_ROLE_KEY": "test-key",
        }):
            config = SupabaseConfig.from_env()
            assert config.project_ref == "test-ref"
            assert config.service_role_key == "test-key"

    def test_from_env_missing_project_ref(self):
        """Test config fails without project ref."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="SUPABASE_PROJECT_REF"):
                SupabaseConfig.from_env()

    def test_from_env_missing_service_role_key(self):
        """Test config fails without service role key."""
        with patch.dict(os.environ, {
            "SUPABASE_PROJECT_REF": "test-ref",
        }, clear=True):
            with pytest.raises(ValueError, match="SUPABASE_SERVICE_ROLE_KEY"):
                SupabaseConfig.from_env()

    def test_api_url_property(self):
        """Test API URL property."""
        config = SupabaseConfig(
            project_ref="test-ref",
            service_role_key="test-key",
        )
        assert config.api_url == "https://test-ref.supabase.co"

        config.base_url = "https://custom.url"
        assert config.api_url == "https://custom.url"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
