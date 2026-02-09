#!/usr/bin/env python3
"""
Test suite for paths.py path resolution library.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from paths import (
    PathResolver,
    get_path_resolver,
    get_blackbox5_root,
    get_engine_path,
    get_memory_root,
    get_routes_path,
    reset_path_resolver
)


class TestPathResolver:
    """Test PathResolver class."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_path_resolver()

    def test_blackbox5_root_default(self):
        """Test default BlackBox5 root path."""
        resolver = PathResolver()
        expected = Path.home() / '.blackbox5'
        assert resolver.blackbox5_root == expected

    def test_blackbox5_root_from_env(self):
        """Test BlackBox5 root from environment variable."""
        with patch.dict(os.environ, {'BLACKBOX5_HOME': '/custom/path'}):
            resolver = PathResolver()
            assert resolver.blackbox5_root == Path('/custom/path')

    def test_engine_path_default(self):
        """Test default engine path resolution."""
        resolver = PathResolver()
        # Should be parent of lib directory
        expected = Path(__file__).parent.parent
        assert resolver.engine_path == expected

    def test_engine_path_from_env(self):
        """Test engine path from environment variable."""
        with patch.dict(os.environ, {'BB5_ENGINE_ROOT': '/custom/engine'}):
            resolver = PathResolver()
            assert resolver.engine_path == Path('/custom/engine')

    def test_memory_root_default(self):
        """Test default memory root path."""
        resolver = PathResolver()
        expected = resolver.blackbox5_root / '5-project-memory'
        assert resolver.memory_root == expected

    def test_memory_root_from_env(self):
        """Test memory root from environment variable."""
        with patch.dict(os.environ, {'BB5_MEMORY_PATH': '/custom/memory'}):
            resolver = PathResolver()
            assert resolver.memory_root == Path('/custom/memory')

    def test_lib_path(self):
        """Test lib path resolution."""
        resolver = PathResolver()
        expected = resolver.engine_path / '.autonomous' / 'lib'
        assert resolver.lib_path == expected

    def test_config_path(self):
        """Test config path resolution."""
        resolver = PathResolver()
        expected = resolver.engine_path / '.autonomous' / 'config'
        assert resolver.config_path == expected

    def test_prompts_path(self):
        """Test prompts path resolution."""
        resolver = PathResolver()
        expected = resolver.engine_path / '.autonomous' / 'prompts'
        assert resolver.prompts_path == expected

    def test_hooks_path(self):
        """Test hooks path resolution."""
        resolver = PathResolver()
        expected = resolver.engine_path / '.autonomous' / 'hooks'
        assert resolver.hooks_path == expected

    def test_templates_path(self):
        """Test templates path resolution."""
        resolver = PathResolver()
        expected = resolver.engine_path / '.autonomous' / 'templates'
        assert resolver.templates_path == expected

    def test_docs_root(self):
        """Test docs root path."""
        resolver = PathResolver()
        expected = resolver.blackbox5_root / '1-docs'
        assert resolver.docs_root == expected

    def test_bin_root(self):
        """Test bin root path."""
        resolver = PathResolver()
        expected = resolver.blackbox5_root / 'bin'
        assert resolver.bin_root == expected

    def test_roadmap_root(self):
        """Test roadmap root path."""
        resolver = PathResolver()
        expected = resolver.blackbox5_root / '6-roadmap'
        assert resolver.roadmap_root == expected

    def test_get_project_path(self):
        """Test project path resolution."""
        resolver = PathResolver(project_name='testproject')
        expected = resolver.memory_root / 'testproject'
        assert resolver.get_project_path() == expected
        assert resolver.get_project_path('other') == resolver.memory_root / 'other'

    def test_get_project_config_path(self):
        """Test project config path."""
        resolver = PathResolver(project_name='testproject')
        expected = resolver.get_project_path() / '.autonomous' / 'config' / 'project.yaml'
        assert resolver.get_project_config_path() == expected

    def test_get_runs_path(self):
        """Test runs path resolution."""
        resolver = PathResolver(project_name='testproject')
        expected = resolver.get_project_path() / '.autonomous' / 'runs'
        assert resolver.get_runs_path() == expected

    def test_get_tasks_path(self):
        """Test tasks path resolution."""
        resolver = PathResolver(project_name='testproject')
        expected = resolver.get_project_path() / '.autonomous' / 'tasks' / 'active'
        assert resolver.get_tasks_path() == expected
        assert resolver.get_tasks_path(status='completed') == resolver.get_project_path() / '.autonomous' / 'tasks' / 'completed'

    def test_get_memory_path(self):
        """Test memory path resolution."""
        resolver = PathResolver(project_name='testproject')
        expected = resolver.get_project_path() / '.autonomous' / 'memory'
        assert resolver.get_memory_path() == expected

    def test_get_analysis_path(self):
        """Test analysis path resolution."""
        resolver = PathResolver(project_name='testproject')
        expected = resolver.get_project_path() / '.autonomous' / 'analysis'
        assert resolver.get_analysis_path() == expected

    def test_get_timeline_path(self):
        """Test timeline path resolution."""
        resolver = PathResolver(project_name='testproject')
        expected = resolver.get_project_path() / '.autonomous' / 'timeline'
        assert resolver.get_timeline_path() == expected

    def test_get_routes_path(self):
        """Test routes.yaml path."""
        resolver = PathResolver()
        expected = resolver.engine_path / '.autonomous' / 'config' / 'routes.yaml'
        assert resolver.get_routes_path() == expected

    def test_get_run_path(self):
        """Test specific run path."""
        resolver = PathResolver(project_name='testproject')
        expected = resolver.get_runs_path() / 'run-001'
        assert resolver.get_run_path('run-001') == expected

    def test_get_task_path(self):
        """Test specific task path."""
        resolver = PathResolver(project_name='testproject')
        # By default, should return active path (even if doesn't exist)
        expected = resolver.get_tasks_path('testproject', 'active') / 'TASK-001'
        result = resolver.get_task_path('TASK-001')
        assert result == expected

    def test_get_path(self):
        """Test custom path building."""
        resolver = PathResolver()
        expected = resolver.blackbox5_root / 'custom' / 'path'
        assert resolver.get_path('custom', 'path') == expected

    def test_get_engine_path_method(self):
        """Test engine-relative path building."""
        resolver = PathResolver()
        expected = resolver.engine_path / 'subdir' / 'file.txt'
        assert resolver.get_engine_path('subdir', 'file.txt') == expected

    def test_get_project_subpath(self):
        """Test project-relative path building."""
        resolver = PathResolver(project_name='testproject')
        expected = resolver.get_project_path() / 'subdir' / 'file.txt'
        assert resolver.get_project_subpath('subdir', 'file.txt') == expected

    def test_ensure_dir(self, tmp_path):
        """Test directory creation."""
        resolver = PathResolver()
        test_dir = tmp_path / 'test_create'
        result = resolver.ensure_dir(test_dir)
        assert result == Path(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_exists(self, tmp_path):
        """Test path existence check."""
        resolver = PathResolver()
        test_file = tmp_path / 'test.txt'
        test_file.write_text('test')
        assert resolver.exists(test_file) is True
        assert resolver.exists(tmp_path / 'nonexistent') is False


class TestGlobalFunctions:
    """Test global convenience functions."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_path_resolver()

    def test_get_path_resolver_caching(self):
        """Test that get_path_resolver caches instances."""
        r1 = get_path_resolver()
        r2 = get_path_resolver()
        assert r1 is r2

    def test_get_path_resolver_different_project(self):
        """Test that different project names create new instances."""
        r1 = get_path_resolver('project1')
        r2 = get_path_resolver('project2')
        assert r1 is not r2
        assert r1.project_name == 'project1'
        assert r2.project_name == 'project2'

    def test_get_blackbox5_root(self):
        """Test global get_blackbox5_root function."""
        result = get_blackbox5_root()
        assert result == Path.home() / '.blackbox5'

    def test_get_engine_path(self):
        """Test global get_engine_path function."""
        result = get_engine_path()
        expected = Path(__file__).parent.parent
        assert result == expected

    def test_get_memory_root(self):
        """Test global get_memory_root function."""
        result = get_memory_root()
        expected = get_path_resolver().memory_root
        assert result == expected

    def test_get_routes_path(self):
        """Test global get_routes_path function."""
        result = get_routes_path()
        expected = get_path_resolver().get_routes_path()
        assert result == expected


def run_tests():
    """Run all tests."""
    import tempfile

    print("=" * 60)
    print("Testing Path Resolution Library")
    print("=" * 60)

    # Create temporary directory for tests that need it
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        test_resolver = TestPathResolver()
        test_globals = TestGlobalFunctions()

        tests_run = 0
        tests_passed = 0
        tests_failed = 0

        # Run all test methods
        for test_class in [test_resolver, test_globals]:
            for method_name in dir(test_class):
                if method_name.startswith('test_'):
                    tests_run += 1
                    try:
                        test_class.setup_method()
                        method = getattr(test_class, method_name)
                        # Check if method needs tmp_path
                        import inspect
                        sig = inspect.signature(method)
                        if 'tmp_path' in sig.parameters:
                            method(tmp_path)
                        else:
                            method()
                        print(f"  PASS: {method_name}")
                        tests_passed += 1
                    except Exception as e:
                        print(f"  FAIL: {method_name} - {e}")
                        tests_failed += 1

    print()
    print("=" * 60)
    print(f"Tests Run: {tests_run}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print("=" * 60)

    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
