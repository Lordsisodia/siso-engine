#!/usr/bin/env python3
"""
Tests for LLMLingua Compression Verification Script.
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestCheckLLMLinguaInstallation:
    """Tests for check_llmlingua_installation function."""

    def test_llmlingua_installed(self, monkeypatch):
        """Test successful LLMLingua installation check."""
        # Create a mock llmlingua module
        mock_llmlingua = MagicMock()
        mock_llmlingua.__version__ = "0.1.0"

        # Patch import to return our mock
        import importlib
        original_import = importlib.import_module

        def mock_import(name, *args, **kwargs):
            if name == "llmlingua":
                return mock_llmlingua
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        # Import after patching
        import importlib
        verify_module = importlib.import_module("verify_compression_setup")

        # Capture output
        with patch("builtins.print") as mock_print:
            result = verify_module.check_llmlingua_installation(verbose=False)

        assert result is True
        mock_print.assert_called()

    def test_llmlingua_not_installed(self, monkeypatch):
        """Test LLMLingua not installed scenario."""
        import importlib
        original_import = importlib.import_module

        def mock_import(name, *args, **kwargs):
            if name == "llmlingua":
                raise ImportError("No module named 'llmlingua'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        import importlib
        verify_module = importlib.import_module("verify_compression_setup")

        with patch("builtins.print") as mock_print:
            result = verify_module.check_llmlingua_installation(verbose=False)

        assert result is False
        mock_print.assert_called()


class TestCheckHuggingFaceAuth:
    """Tests for check_huggingface_auth function."""

    def test_authenticated(self, monkeypatch):
        """Test successful HuggingFace authentication."""
        mock_whoami = MagicMock()
        mock_whoami.return_value = {"name": "testuser"}

        monkeypatch.setattr("huggingface_hub.whoami", mock_whoami)

        import importlib
        verify_module = importlib.import_module("verify_compression_setup")

        with patch("builtins.print") as mock_print:
            result = verify_module.check_huggingface_auth(verbose=False)

        assert result is True
        mock_print.assert_called()

    def test_not_authenticated(self, monkeypatch):
        """Test failed HuggingFace authentication."""
        from huggingface_hub import HfHubError

        mock_whoami = MagicMock()
        mock_whoami.side_effect = HfHubError("Not authenticated")

        monkeypatch.setattr("huggingface_hub.whoami", mock_whoami)

        import importlib
        verify_module = importlib.import_module("verify_compression_setup")

        with patch("builtins.print") as mock_print:
            result = verify_module.check_huggingface_auth(verbose=False)

        assert result is False
        mock_print.assert_called()


class TestSimpleCompress:
    """Tests for simple_compress function."""

    def test_simple_compress_removes_filler_words(self, monkeypatch):
        """Test that simple_compress removes filler words."""
        import importlib
        verify_module = importlib.import_module("verify_compression_setup")

        text = "The quick brown fox and the lazy dog"
        result = verify_module.simple_compress(text)

        # Should remove 'the', 'and'
        assert "The" not in result
        assert "and" not in result
        assert "quick" in result
        assert "brown" in result

    def test_simple_compress_preserves_content_words(self, monkeypatch):
        """Test that simple_compress preserves content words."""
        import importlib
        verify_module = importlib.import_module("verify_compression_setup")

        text = "This is a test prompt for compression"
        result = verify_module.simple_compress(text)

        assert "test" in result
        assert "prompt" in result
        assert "compression" in result

    def test_simple_compress_empty_string(self, monkeypatch):
        """Test simple_compress with empty string."""
        import importlib
        verify_module = importlib.import_module("verify_compression_setup")

        result = verify_module.simple_compress("")
        assert result == ""


class TestDisplayCostSavings:
    """Tests for display_cost_savings function."""

    def test_display_cost_savings_output(self, monkeypatch):
        """Test cost savings display with known compression ratio."""
        import importlib
        verify_module = importlib.import_module("verify_compression_setup")

        with patch("builtins.print") as mock_print:
            verify_module.display_cost_savings(90.0, "llmlingua")

        # Verify print was called multiple times for the table
        assert mock_print.call_count > 5

        # Check that some expected strings are in output
        printed_strings = [str(call) for call in mock_print.call_args_list]
        output = "\n".join(printed_strings)
        assert "90.0%" in output or "90" in output
        assert "$" in output  # Currency symbol


class TestMain:
    """Tests for main function."""

    def test_main_with_verbose_flag(self, monkeypatch):
        """Test main function with verbose flag."""
        import importlib
        verify_module = importlib.import_module("verify_compression_setup")

        # Mock all the check functions to return True
        with patch.object(verify_module, "check_llmlingua_installation", return_value=True), \
             patch.object(verify_module, "check_huggingface_auth", return_value=True), \
             patch.object(verify_module, "test_llama_model_access", return_value=True), \
             patch.object(verify_module, "test_compression", return_value=(True, 90.0, "llmlingua")), \
             patch.object(verify_module, "display_cost_savings"), \
             patch("sys.argv", ["verify_compression_setup.py", "-v"]):

            result = verify_module.main()
            assert result == 0

    def test_main_failure_case(self, monkeypatch):
        """Test main function when checks fail."""
        import importlib
        verify_module = importlib.import_module("verify_compression_setup")

        # Mock check functions to return False
        with patch.object(verify_module, "check_llmlingua_installation", return_value=False), \
             patch.object(verify_module, "check_huggingface_auth", return_value=False), \
             patch.object(verify_module, "test_llama_model_access", return_value=False), \
             patch.object(verify_module, "test_compression", return_value=(False, 0.0, "unavailable")):

            result = verify_module.main()
            assert result == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
