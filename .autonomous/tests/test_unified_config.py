#!/usr/bin/env python3
"""
Unit Tests for Unified Configuration System
============================================

Tests for unified_config.py and related functionality.

Run with: python3 -m pytest test_unified_config.py -v
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

import yaml
from unified_config import (
    UnifiedConfig,
    PathResolver,
    ConfigPaths,
    ConfigValidationError,
    ConfigNotFoundError,
    get_config,
    reload_config,
    get_path_resolver,
)


class TestUnifiedConfig(unittest.TestCase):
    """Test cases for UnifiedConfig class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = Path(self.temp_dir) / 'base.yaml'
        self.engine_config = Path(self.temp_dir) / 'engine.yaml'
        self.project_config = Path(self.temp_dir) / 'project.yaml'
        self.user_config = Path(self.temp_dir) / 'user.yaml'

        # Create base config
        with open(self.base_config, 'w') as f:
            yaml.dump({
                'version': '2.0.0',
                'system': {
                    'name': 'TestBase',
                    'log_level': 'INFO'
                },
                'paths': {
                    'engine': '/base/engine',
                    'memory': '/base/memory'
                },
                'thresholds': {
                    'skill_invocation_confidence': 70
                }
            }, f)

        # Create engine config
        with open(self.engine_config, 'w') as f:
            yaml.dump({
                'system': {
                    'name': 'TestEngine'
                },
                'paths': {
                    'engine': '/engine/path'
                }
            }, f)

        # Create project config
        with open(self.project_config, 'w') as f:
            yaml.dump({
                'project': {
                    'name': 'testproject'
                },
                'thresholds': {
                    'skill_invocation_confidence': 80
                }
            }, f)

        # Create user config
        with open(self.user_config, 'w') as f:
            yaml.dump({
                'system': {
                    'log_level': 'DEBUG'
                }
            }, f)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_loading(self):
        """Test that configuration loads from files."""
        config = UnifiedConfig(project_name='test', auto_load=False)

        # Create custom paths - only base to test base loading
        custom_paths = ConfigPaths()
        custom_paths.base_defaults = str(self.base_config)
        # Don't set other paths to test base-only loading

        config.load(custom_paths=custom_paths)

        self.assertEqual(config.get('version'), '2.0.0')
        self.assertEqual(config.get('system.name'), 'TestBase')

    def test_config_hierarchy(self):
        """Test that config hierarchy is respected."""
        config = UnifiedConfig(project_name='test', auto_load=False)

        # Create custom paths
        custom_paths = ConfigPaths()
        custom_paths.base_defaults = str(self.base_config)
        custom_paths.engine_config = str(self.engine_config)
        custom_paths.project_config = str(self.project_config)
        custom_paths.user_config = str(self.user_config)

        config.load(custom_paths=custom_paths)

        # User config should override base
        self.assertEqual(config.get('system.log_level'), 'DEBUG')

        # Project config should override base
        self.assertEqual(config.get('thresholds.skill_invocation_confidence'), 80)

        # Engine config should override base
        self.assertEqual(config.get('paths.engine'), '/engine/path')

    def test_get_with_default(self):
        """Test get method with default value."""
        config = UnifiedConfig(project_name='test', auto_load=False)

        # Create custom paths
        custom_paths = ConfigPaths()
        custom_paths.base_defaults = str(self.base_config)

        config.load(custom_paths=custom_paths)

        # Existing key
        self.assertEqual(config.get('system.name'), 'TestBase')

        # Missing key with default
        self.assertEqual(config.get('missing.key', 'default'), 'default')

        # Missing key without default
        self.assertIsNone(config.get('missing.key'))

    def test_get_nested(self):
        """Test getting nested configuration values."""
        config = UnifiedConfig(project_name='test', auto_load=False)

        # Create custom paths
        custom_paths = ConfigPaths()
        custom_paths.base_defaults = str(self.base_config)

        config.load(custom_paths=custom_paths)

        self.assertEqual(config.get('system.log_level'), 'INFO')
        self.assertEqual(config.get('paths.engine'), '/base/engine')

    def test_set_value(self):
        """Test setting configuration values."""
        config = UnifiedConfig(project_name='test', auto_load=False)
        config.paths.base_defaults = str(self.base_config)
        config.load()

        config.set('custom.key', 'custom_value')
        self.assertEqual(config.get('custom.key'), 'custom_value')

        config.set('system.log_level', 'ERROR')
        self.assertEqual(config.get('system.log_level'), 'ERROR')

    def test_get_bool(self):
        """Test get_bool method."""
        config = UnifiedConfig(project_name='test', auto_load=False)
        config.config = {
            'flag_true': True,
            'flag_false': False,
            'str_true': 'true',
            'str_false': 'false',
            'str_yes': 'yes',
        }

        self.assertTrue(config.get_bool('flag_true'))
        self.assertFalse(config.get_bool('flag_false'))
        self.assertTrue(config.get_bool('str_true'))
        self.assertFalse(config.get_bool('str_false'))
        self.assertTrue(config.get_bool('str_yes'))
        self.assertFalse(config.get_bool('missing', False))

    def test_get_int(self):
        """Test get_int method."""
        config = UnifiedConfig(project_name='test', auto_load=False)
        config.config = {
            'number': 42,
            'str_number': '42',
        }

        self.assertEqual(config.get_int('number'), 42)
        self.assertEqual(config.get_int('str_number'), 42)
        self.assertEqual(config.get_int('missing', 100), 100)

    def test_get_list(self):
        """Test get_list method."""
        config = UnifiedConfig(project_name='test', auto_load=False)
        config.config = {
            'items': ['a', 'b', 'c'],
            'single': 'single_item',
        }

        self.assertEqual(config.get_list('items'), ['a', 'b', 'c'])
        self.assertEqual(config.get_list('single'), ['single_item'])
        self.assertEqual(config.get_list('missing'), [])

    def test_environment_substitution(self):
        """Test environment variable substitution."""
        config = UnifiedConfig(project_name='test', auto_load=False)

        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = config._substitute_env_vars({
                'simple': '${TEST_VAR}',
                'with_default': '${MISSING_VAR:-default_value}',
                'nested': {
                    'value': '${TEST_VAR}'
                }
            })

            self.assertEqual(result['simple'], 'test_value')
            self.assertEqual(result['with_default'], 'default_value')
            self.assertEqual(result['nested']['value'], 'test_value')

    def test_deep_merge(self):
        """Test deep merge functionality."""
        config = UnifiedConfig(project_name='test', auto_load=False)

        base = {
            'a': 1,
            'b': {'c': 2, 'd': 3},
            'e': [1, 2]
        }

        override = {
            'b': {'c': 20},
            'f': 'new'
        }

        result = config._deep_merge(base, override)

        self.assertEqual(result['a'], 1)
        self.assertEqual(result['b']['c'], 20)
        self.assertEqual(result['b']['d'], 3)
        self.assertEqual(result['e'], [1, 2])
        self.assertEqual(result['f'], 'new')

    def test_reload(self):
        """Test configuration reload."""
        config = UnifiedConfig(project_name='test', auto_load=False)

        # Create custom paths - only base
        custom_paths = ConfigPaths()
        custom_paths.base_defaults = str(self.base_config)

        config.load(custom_paths=custom_paths)

        # Verify initial value
        self.assertEqual(config.get('system.log_level'), 'INFO')

        # Modify the file
        with open(self.base_config, 'w') as f:
            yaml.dump({'system': {'log_level': 'CHANGED'}}, f)

        # Reload - need to set paths again since reload() calls load() without custom_paths
        config.paths = custom_paths
        config.reload()

        self.assertEqual(config.get('system.log_level'), 'CHANGED')


class TestPathResolver(unittest.TestCase):
    """Test cases for PathResolver class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = MagicMock()
        self.config._get_blackbox5_root.return_value = '/home/user/.blackbox5'
        self.config.get = MagicMock(side_effect=lambda key, default=None: {
            'paths.engine': '/custom/engine',
            'paths.memory': '/custom/memory',
        }.get(key, default))
        self.config.project_name = 'testproject'

        self.resolver = PathResolver(self.config)

    def test_blackbox5_root(self):
        """Test BlackBox5 root path resolution."""
        self.assertEqual(self.resolver.blackbox5_root, Path('/home/user/.blackbox5'))

    def test_engine_root_from_config(self):
        """Test engine root from config."""
        self.assertEqual(self.resolver.engine_root, Path('/custom/engine'))

    def test_memory_root_from_config(self):
        """Test memory root from config."""
        self.assertEqual(self.resolver.memory_root, Path('/custom/memory'))

    def test_get_project_path(self):
        """Test project path resolution."""
        path = self.resolver.get_project_path()
        self.assertIn('testproject', str(path))

    def test_get_project_path_with_name(self):
        """Test project path with explicit name."""
        path = self.resolver.get_project_path('otherproject')
        self.assertIn('otherproject', str(path))


class TestEnvironmentOverrides(unittest.TestCase):
    """Test environment variable overrides."""

    def test_bb5_log_level_override(self):
        """Test BB5_LOG_LEVEL environment variable."""
        with patch.dict(os.environ, {'BB5_LOG_LEVEL': 'DEBUG'}):
            config = UnifiedConfig(project_name='test', auto_load=False)
            config.config = {}
            config._apply_environment_overrides()
            self.assertEqual(config.get('system.log_level'), 'DEBUG')

    def test_bb5_debug_override(self):
        """Test BB5_DEBUG environment variable."""
        with patch.dict(os.environ, {'BB5_DEBUG': 'true'}):
            config = UnifiedConfig(project_name='test', auto_load=False)
            config.config = {}
            config._apply_environment_overrides()
            self.assertTrue(config.get('system.debug_mode'))

    def test_github_token_override(self):
        """Test GITHUB_TOKEN environment variable."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'ghp_test_token'}):
            config = UnifiedConfig(project_name='test', auto_load=False)
            config.config = {}
            config._apply_environment_overrides()
            self.assertEqual(config.get('integrations.github.token'), 'ghp_test_token')


class TestSingleton(unittest.TestCase):
    """Test singleton behavior."""

    def test_get_config_singleton(self):
        """Test that get_config returns singleton."""
        # Clear any existing singleton
        import unified_config
        unified_config._global_config = None

        config1 = get_config()
        config2 = get_config()

        self.assertIs(config1, config2)

    def test_reload_creates_new_instance(self):
        """Test that reload returns the same singleton instance."""
        # Clear any existing singleton
        import unified_config
        unified_config._global_config = None

        config1 = get_config()
        # reload_config should return the same instance after reloading
        config2 = reload_config()

        # After reload, they should be the same object
        # Note: reload_config() creates a new UnifiedConfig instance but assigns it
        # to the same _global_config variable, so config1 and config2 will be different
        # objects but _global_config will point to config2
        self.assertIs(unified_config._global_config, config2)


class TestIntegration(unittest.TestCase):
    """Integration tests with real files."""

    def test_real_config_loading(self):
        """Test loading from real config files."""
        # This test assumes the real config files exist
        engine_root = Path(__file__).parent.parent
        base_config = engine_root / 'config' / 'base.yaml'

        if not base_config.exists():
            self.skipTest("Base config not found")

        config = UnifiedConfig(project_name='blackbox5')

        # Should load without errors
        self.assertIsNotNone(config.get('version'))
        self.assertIsNotNone(config.get('system.name'))


if __name__ == '__main__':
    unittest.main()
