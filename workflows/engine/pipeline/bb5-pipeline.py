#!/usr/bin/env python3
"""
BlackBox5 CLI with Pipeline Support

Extended CLI with pipeline commands:
- Feature management
- Testing operations
- Unified pipeline execution
"""

import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional

# Add the engine directory to the path
engine_dir = Path(__file__).parent / "engine"
sys.path.insert(0, str(engine_dir))


class PipelineCommands:
    """Pipeline command handlers"""

    def __init__(self, blackbox_root: Path):
        self.blackbox_root = Path(blackbox_root)

        # Import pipeline modules
        from workflows.engine.pipeline.feature_pipeline import FeaturePipeline, FeaturePriority
        from workflows.engine.pipeline.testing_pipeline import TestingPipeline
        from workflows.engine.pipeline.unified_pipeline import UnifiedPipeline

        self.FeaturePipeline = FeaturePipeline
        self.TestingPipeline = TestingPipeline
        self.UnifiedPipeline = UnifiedPipeline
        self.FeaturePriority = FeaturePriority

    def propose_feature(self, args):
        """Propose a new feature"""
        pipeline = self.FeaturePipeline(self.blackbox_root)

        feature = pipeline.propose_feature(
            name=args.name,
            description=args.description,
            source_type=args.source or "internal",
            source_name=args.source_name or "manual",
            priority=self.FeaturePriority(args.priority) if args.priority else self.FeaturePriority.MEDIUM
        )

        print(f"\n✅ Feature Proposed:")
        print(f"   ID: {feature.feature_id}")
        print(f"   Name: {feature.name}")
        print(f"   Priority: {feature.priority.value}")
        print(f"   Status: {feature.status.value}")

    def list_features(self, args):
        """List all features"""
        from workflows.engine.pipeline.feature_pipeline import FeatureStatus

        pipeline = self.FeaturePipeline(self.blackbox_root)

        # Filter by status if specified
        status_filter = None
        if args.status:
            status_filter = FeatureStatus(args.status)

        features = pipeline.get_backlog(status=status_filter)

        print(f"\n📋 Feature Backlog ({len(features)} features)\n")

        if not features:
            print("   No features found.")
            return

        for feature in features:
            emoji = {
                'proposed': '📝',
                'approved': '✅',
                'implementing': '🔨',
                'testing': '🧪',
                'completed': '🎉',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(feature.status.value, '📌')

            print(f"   {emoji} [{feature.feature_id}] {feature.name}")
            print(f"      Status: {feature.status.value} | Priority: {feature.priority.value}")
            if feature.simplified_description:
                print(f"      Description: {feature.simplified_description[:80]}...")
            print()

    def feature_stats(self, args):
        """Show feature statistics"""
        pipeline = self.FeaturePipeline(self.blackbox_root)
        stats = pipeline.get_statistics()

        print(f"\n📊 Pipeline Statistics\n")
        print(f"   Total in backlog: {stats['total_in_backlog']}")
        print(f"   Total completed: {stats['total_completed']}")

        print(f"\n   By Status:")
        for status, count in stats['by_status'].items():
            if count > 0:
                print(f"      {status}: {count}")

        print(f"\n   By Priority:")
        for priority, count in stats['by_priority'].items():
            if count > 0:
                print(f"      {priority}: {count}")

    def run_tests(self, args):
        """Run test suite"""
        async def run():
            pipeline = self.TestingPipeline(self.blackbox_root)

            result = await pipeline.run_test_suite(
                test_pattern=args.pattern or "test_*.py",
                max_iterations=args.iterations or 3
            )

            print(f"\n📊 Test Results:")
            print(f"   Total: {result.total_tests}")
            print(f"   Passed: {result.passed} ✅")
            print(f"   Failed: {result.failed} ❌")
            print(f"   Skipped: {result.skipped} ⏭️")
            print(f"   Duration: {result.duration:.2f}s")
            print(f"   Status: {result.status.value}")

            if result.failed > 0:
                print(f"\n⚠️  Failed Tests:")
                for failure in result.failures[:5]:
                    print(f"   - {failure.test_name}")

        asyncio.run(run())

    def test_history(self, args):
        """Show test history"""
        pipeline = self.TestingPipeline(self.blackbox_root)
        history = pipeline.get_test_history(limit=args.limit or 10)

        print(f"\n📜 Recent Test Runs ({len(history)})\n")

        for result in history:
            status_emoji = "✅" if result.status.value == "passed" else "❌"
            print(f"   {status_emoji} {result.timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"      {result.passed}/{result.total_tests} passed in {result.duration:.2f}s")
            print()

    def pipeline_history(self, args):
        """Show unified pipeline history"""
        pipeline = self.UnifiedPipeline(self.blackbox_root)
        history = pipeline.get_run_history(limit=args.limit or 10)

        print(f"\n📜 Pipeline Run History ({len(history)})\n")

        for run in history:
            phase_emoji = "✅" if run.phase.value == "completed" else "❌"
            print(f"   {phase_emoji} {run.started_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"      Feature: {run.feature.name}")
            print(f"      Phase: {run.phase.value}")

            if run.completed_at:
                duration = (run.completed_at - run.started_at).total_seconds()
                print(f"      Duration: {duration:.1f}s")
            print()

    def integration_status(self, args):
        """Show pipeline integration status"""
        from workflows.engine.pipeline.pipeline_integration import get_pipeline_integration

        integration = get_pipeline_integration(self.blackbox_root)
        integration.log_pipeline_summary()


def add_pipeline_commands(parser: argparse.ArgumentParser):
    """Add pipeline-related commands to the argument parser"""

    subparsers = parser.add_subparsers(
        dest="command",
        help="Pipeline commands"
    )

    # Feature propose command
    propose_parser = subparsers.add_parser(
        "propose",
        help="Propose a new feature"
    )
    propose_parser.add_argument("--name", required=True, help="Feature name")
    propose_parser.add_argument("--description", required=True, help="Feature description")
    propose_parser.add_argument("--source", help="Source type")
    propose_parser.add_argument("--source-name", help="Source name")
    propose_parser.add_argument("--priority", help="Priority level")

    # Feature list command
    list_parser = subparsers.add_parser(
        "list-features",
        help="List all features"
    )
    list_parser.add_argument("--status", help="Filter by status")

    # Feature stats command
    subparsers.add_parser("stats", help="Show feature statistics")

    # Test run command
    test_parser = subparsers.add_parser(
        "test",
        help="Run test suite"
    )
    test_parser.add_argument("--pattern", help="Test pattern")
    test_parser.add_argument("--iterations", type=int, help="Max fix iterations")

    # Test history command
    history_parser = subparsers.add_parser(
        "test-history",
        help="Show test history"
    )
    history_parser.add_argument("--limit", type=int, help="Number of runs to show")

    # Pipeline history command
    pipeline_history_parser = subparsers.add_parser(
        "pipeline-history",
        help="Show pipeline run history"
    )
    pipeline_history_parser.add_argument("--limit", type=int, help="Number of runs to show")

    # Integration status command
    subparsers.add_parser("integration", help="Show integration status")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BlackBox5 CLI with Pipeline Support",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Global options
    parser.add_argument(
        "--blackbox",
        type=str,
        default=".",
        help="Path to BlackBox5 root"
    )

    # Add pipeline commands
    add_pipeline_commands(parser)

    args = parser.parse_args()

    # Determine blackbox root
    blackbox_root = Path(args.blackbox)

    if not args.command:
        parser.print_help()
        return

    # Execute command
    commands = PipelineCommands(blackbox_root)

    if args.command == "propose":
        commands.propose_feature(args)
    elif args.command == "list-features":
        commands.list_features(args)
    elif args.command == "stats":
        commands.feature_stats(args)
    elif args.command == "test":
        commands.run_tests(args)
    elif args.command == "test-history":
        commands.test_history(args)
    elif args.command == "pipeline-history":
        commands.pipeline_history(args)
    elif args.command == "integration":
        commands.integration_status(args)


if __name__ == "__main__":
    main()
