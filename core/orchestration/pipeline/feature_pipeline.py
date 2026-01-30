#!/usr/bin/env python3
"""
Feature Pipeline System for BlackBox5

Automates the process of reviewing, implementing, and testing features
using GSD (Goal-Backward Solo Development) framework.

Pipeline Flow:
1. Feature Discovery → Feature Backlog
2. Feature Review & Simplification
3. Feature Breakdown → GSD Tasks
4. Implementation Loop (with testing)
5. Quality Validation
6. Integration & Documentation
"""

import asyncio
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import yaml

from .Orchestrator import AgentOrchestrator, WorkflowStep, WorkflowResult
from .context_extractor import ContextExtractor
from .pipeline_integration import get_pipeline_integration


class FeatureStatus(str, Enum):
    """Status of a feature in the pipeline"""
    PROPOSED = "proposed"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    SIMPLIFYING = "simplifying"
    BREAKING_DOWN = "breaking_down"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class FeaturePriority(str, Enum):
    """Priority levels for features"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FeatureSource:
    """Where a feature came from"""
    type: str  # "framework", "user_request", "internal", "refactor"
    name: str  # e.g., "AgentScope", "DeerFlow", "User feedback"
    url: Optional[str] = None
    description: str = ""


@dataclass
class Feature:
    """
    Represents a feature to be implemented.

    Attributes:
        feature_id: Unique identifier
        name: Short feature name
        description: Detailed description
        source: Where this feature came from
        priority: Priority level
        status: Current status
        simplified_description: Simplified/core essence after review
        acceptance_criteria: List of acceptance criteria
        dependencies: List of feature IDs this depends on
        implementation_notes: Notes from implementation phase
        test_results: Test execution results
        created_at: When feature was proposed
        updated_at: Last update timestamp
        metadata: Additional metadata
    """
    feature_id: str
    name: str
    description: str
    source: FeatureSource
    priority: FeaturePriority = FeaturePriority.MEDIUM
    status: FeatureStatus = FeatureStatus.PROPOSED
    simplified_description: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    implementation_notes: str = ""
    test_results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to strings
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        # Convert source
        data['source'] = asdict(self.source)
        # Convert datetime to ISO format
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feature':
        """Create from dictionary"""
        # Convert source
        if 'source' in data and isinstance(data['source'], dict):
            data['source'] = FeatureSource(**data['source'])
        # Convert enums
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = FeaturePriority(data['priority'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = FeatureStatus(data['status'])
        # Convert datetime
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        # Generate feature_id if not present
        if 'feature_id' not in data:
            import uuid
            data['feature_id'] = str(uuid.uuid4())
        return cls(**data)


class FeatureReviewAgent:
    """
    AI-powered feature review and simplification agent.

    Uses first principles and reasoning to:
    1. Review proposed features
    2. Identify core value/essence
    3. Simplify and remove complexity
    4. Generate acceptance criteria
    """

    def __init__(self, context_extractor: ContextExtractor):
        self.context_extractor = context_extractor

    async def review_feature(self, feature: Feature) -> Dict[str, Any]:
        """
        Review a feature and provide recommendations.

        Returns:
            Dictionary with:
            - should_implement: bool
            - simplified_description: str
            - acceptance_criteria: List[str]
            - complexity_estimate: str
            - reasoning: str
            - concerns: List[str]
        """
        # Extract context about the codebase
        context = await self.context_extractor.extract_context(
            task_id=f"review_{feature.feature_id}",
            task_description=f"Review feature: {feature.name}"
        )

        # Analyze the feature
        analysis = await self._analyze_feature(feature, context)

        return analysis

    async def _analyze_feature(self, feature: Feature, context: Any) -> Dict[str, Any]:
        """
        Analyze feature using first principles.

        Key questions:
        1. What problem does this solve?
        2. What is the core value?
        3. What can be simplified?
        4. Is this worth building?
        """
        # This is where the AI reasoning happens
        # For now, use heuristic-based analysis

        # Check for complexity indicators
        description_length = len(feature.description)
        word_count = len(feature.description.split())

        # Extract keywords from description
        keywords = self.context_extractor.extract_keywords(feature.description)

        # Analyze based on source type
        if feature.source.type == "framework":
            # Framework features often need simplification
            should_implement = True
            simplified_description = self._simplify_framework_feature(feature)
            complexity_estimate = "medium"
            reasoning = f"Feature from {feature.source.name} framework. Identified core functionality to implement."
        else:
            should_implement = True
            simplified_description = feature.description
            complexity_estimate = "low"
            reasoning = "User-requested feature with clear scope."

        # Generate acceptance criteria
        acceptance_criteria = self._generate_acceptance_criteria(feature, simplified_description)

        # Identify concerns
        concerns = []
        if word_count > 200:
            concerns.append("Description is very long - consider simplifying further")
        if len(feature.dependencies) > 3:
            concerns.append("Many dependencies - consider breaking into smaller features")

        return {
            "should_implement": should_implement,
            "simplified_description": simplified_description,
            "acceptance_criteria": acceptance_criteria,
            "complexity_estimate": complexity_estimate,
            "reasoning": reasoning,
            "concerns": concerns,
            "keywords": keywords
        }

    def _simplify_framework_feature(self, feature: Feature) -> str:
        """Simplify a framework-derived feature to its core essence."""
        # Extract the core functionality
        description = feature.description.lower()

        # Look for key patterns
        if "middleware" in description:
            return "Middleware system for wrapping agent/tool/model execution"
        elif "token" in description and "compress" in description:
            return "Automatic context compression to fit within token limits"
        elif "yaml" in description or "config" in description:
            return "YAML-based configuration for agents and workflows"
        else:
            # Take first sentence as core
            sentences = feature.description.split('.')
            if sentences:
                return sentences[0].strip()
            return feature.description[:100]

    def _generate_acceptance_criteria(self, feature: Feature, simplified_desc: str) -> List[str]:
        """Generate acceptance criteria for the feature."""
        criteria = [
            f"Feature implements: {simplified_desc}",
            "Tests pass with 100% success rate",
            "Documentation is complete",
            "Integration with existing codebase works",
        ]
        return criteria


class FeatureBreakdownAgent:
    """
    Breaks down features into GSD tasks for implementation.

    Uses the GSD framework to create a workflow with:
    - Research phase (explore codebase)
    - Design phase (create implementation plan)
    - Implementation phase (write code)
    - Testing phase (write and run tests)
    """

    def __init__(self, context_extractor: ContextExtractor):
        self.context_extractor = context_extractor

    async def breakdown_feature(self, feature: Feature) -> List[WorkflowStep]:
        """
        Break down feature into GSD workflow steps.

        Returns:
            List of WorkflowStep with dependencies
        """
        # Extract context for this feature
        context = await self.context_extractor.extract_context(
            task_id=f"breakdown_{feature.feature_id}",
            task_description=feature.simplified_description or feature.description
        )

        # Create workflow steps
        steps = [
            WorkflowStep(
                agent_type="researcher",
                task=f"Research existing codebase for: {feature.name}",
                agent_id=f"{feature.feature_id}_research",
                depends_on=[],
                metadata={"feature_id": feature.feature_id}
            ),
            WorkflowStep(
                agent_type="architect",
                task=f"Design implementation for: {feature.name}",
                agent_id=f"{feature.feature_id}_design",
                depends_on=[f"{feature.feature_id}_research"],
                metadata={"feature_id": feature.feature_id}
            ),
            WorkflowStep(
                agent_type="developer",
                task=f"Implement: {feature.name}",
                agent_id=f"{feature.feature_id}_implement",
                depends_on=[f"{feature.feature_id}_design"],
                metadata={"feature_id": feature.feature_id}
            ),
            WorkflowStep(
                agent_type="tester",
                task=f"Write and run tests for: {feature.name}",
                agent_id=f"{feature.feature_id}_test",
                depends_on=[f"{feature.feature_id}_implement"],
                metadata={"feature_id": feature.feature_id}
            ),
        ]

        return steps


class FeaturePipeline:
    """
    Main feature pipeline orchestrator.

    Manages the complete lifecycle of features from proposal to completion.
    """

    def __init__(
        self,
        blackbox_root: Path,
        enable_compression: bool = True,
        max_tokens_per_task: int = 8000
    ):
        self.blackbox_root = Path(blackbox_root)
        self.pipeline_dir = self.blackbox_root / "blackbox5" / "pipeline"
        self.backlog_file = self.pipeline_dir / "feature_backlog.yaml"
        self.completed_file = self.pipeline_dir / "completed_features.yaml"

        # Ensure directories exist
        self.pipeline_dir.mkdir(parents=True, exist_ok=True)

        # Initialize context extractor
        self.context_extractor = ContextExtractor(
            codebase_path=self.blackbox_root,
            max_context_tokens=max_tokens_per_task
        )

        # Initialize agents
        self.review_agent = FeatureReviewAgent(self.context_extractor)
        self.breakdown_agent = FeatureBreakdownAgent(self.context_extractor)

        # Initialize orchestrator
        self.orchestrator = AgentOrchestrator(
            enable_token_compression=enable_compression,
            max_tokens_per_task=max_tokens_per_task
        )

        # Load backlog
        self.backlog: List[Feature] = self._load_backlog()
        self.completed: List[Feature] = self._load_completed()

        # Initialize integration with SISO-INTERNAL infrastructure
        self.integration = get_pipeline_integration(self.blackbox_root)

    def _load_backlog(self) -> List[Feature]:
        """Load feature backlog from disk"""
        if not self.backlog_file.exists():
            return []

        with open(self.backlog_file, 'r') as f:
            data = yaml.safe_load(f)

        return [Feature.from_dict(item) for item in data.get('features', [])]

    def _save_backlog(self):
        """Save feature backlog to disk"""
        data = {
            'updated_at': datetime.utcnow().isoformat(),
            'total_count': len(self.backlog),
            'features': [f.to_dict() for f in self.backlog]
        }

        with open(self.backlog_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _load_completed(self) -> List[Feature]:
        """Load completed features from disk"""
        if not self.completed_file.exists():
            return []

        with open(self.completed_file, 'r') as f:
            data = yaml.safe_load(f)

        return [Feature.from_dict(item) for item in data.get('features', [])]

    def _save_completed(self):
        """Save completed features to disk"""
        data = {
            'updated_at': datetime.utcnow().isoformat(),
            'total_count': len(self.completed),
            'features': [f.to_dict() for f in self.completed]
        }

        with open(self.completed_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def propose_feature(
        self,
        name: str,
        description: str,
        source_type: str,
        source_name: str,
        priority: FeaturePriority = FeaturePriority.MEDIUM
    ) -> Feature:
        """
        Propose a new feature.

        Args:
            name: Feature name
            description: Detailed description
            source_type: Type of source (framework, user_request, etc.)
            source_name: Name of the source
            priority: Priority level

        Returns:
            Created Feature object
        """
        import uuid

        feature = Feature(
            feature_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            source=FeatureSource(type=source_type, name=source_name),
            priority=priority,
            status=FeatureStatus.PROPOSED
        )

        self.backlog.append(feature)
        self._save_backlog()

        # Publish event and save state via integration
        self.integration.publish_pipeline_event(
            event_type="feature_proposed",
            pipeline_type="feature",
            data={
                "feature_id": feature.feature_id,
                "name": feature.name,
                "priority": feature.priority.value,
                "source": feature.source.name
            }
        )

        self.integration.save_pipeline_state(
            pipeline_type="feature",
            run_id=feature.feature_id,
            state=feature.to_dict()
        )

        return feature

    async def review_feature(self, feature_id: str) -> Feature:
        """
        Review a feature using AI agent.

        Args:
            feature_id: ID of feature to review

        Returns:
            Updated feature with review results
        """
        feature = self._get_feature(feature_id)
        if not feature:
            raise ValueError(f"Feature {feature_id} not found")

        feature.status = FeatureStatus.REVIEWING
        self._save_backlog()

        # Run review
        review = await self.review_agent.review_feature(feature)

        # Update feature with review results
        if review['should_implement']:
            feature.status = FeatureStatus.APPROVED
            feature.simplified_description = review['simplified_description']
            feature.acceptance_criteria = review['acceptance_criteria']
            feature.metadata['review'] = review
        else:
            feature.status = FeatureStatus.CANCELLED
            feature.metadata['review'] = review

        feature.updated_at = datetime.utcnow()
        self._save_backlog()

        # Publish event and save state via integration
        self.integration.publish_pipeline_event(
            event_type="feature_reviewed",
            pipeline_type="feature",
            data={
                "feature_id": feature.feature_id,
                "status": feature.status.value,
                "approved": review['should_implement']
            }
        )

        self.integration.save_pipeline_state(
            pipeline_type="feature",
            run_id=feature.feature_id,
            state=feature.to_dict()
        )

        return feature

    async def implement_feature(self, feature_id: str) -> Dict[str, Any]:
        """
        Implement a feature using GSD workflow.

        Args:
            feature_id: ID of feature to implement

        Returns:
            Implementation results
        """
        feature = self._get_feature(feature_id)
        if not feature:
            raise ValueError(f"Feature {feature_id} not found")

        feature.status = FeatureStatus.IMPLEMENTING
        self._save_backlog()

        try:
            # Break down feature into GSD tasks
            steps = await self.breakdown_agent.breakdown_down(feature)

            # Execute workflow
            result: WorkflowResult = await self.orchestrator.execute_wave_based(
                steps,
                workflow_id=f"feature_{feature_id}"
            )

            # Update feature with results
            if result.state.value == "completed":
                feature.status = FeatureStatus.TESTING
                feature.test_results = {
                    'workflow_completed': True,
                    'steps_completed': result.steps_completed,
                    'steps_total': result.steps_total,
                    'waves_executed': result.waves_completed
                }
            else:
                feature.status = FeatureStatus.FAILED
                feature.test_results = {
                    'workflow_completed': False,
                    'errors': result.errors
                }

            feature.updated_at = datetime.utcnow()
            self._save_backlog()

            return {
                'feature': feature,
                'workflow_result': result
            }

        except Exception as e:
            feature.status = FeatureStatus.FAILED
            feature.implementation_notes = f"Implementation failed: {str(e)}"
            feature.updated_at = datetime.utcnow()
            self._save_backlog()

            raise

    def get_backlog(self, status: Optional[FeatureStatus] = None) -> List[Feature]:
        """
        Get features from backlog.

        Args:
            status: Optional status filter

        Returns:
            List of features
        """
        if status:
            return [f for f in self.backlog if f.status == status]
        return self.backlog.copy()

    def get_feature(self, feature_id: str) -> Optional[Feature]:
        """Get a specific feature by ID"""
        return self._get_feature(feature_id)

    def _get_feature(self, feature_id: str) -> Optional[Feature]:
        """Internal method to get feature from backlog"""
        for feature in self.backlog:
            if feature.feature_id == feature_id:
                return feature
        return None

    def mark_completed(self, feature_id: str):
        """Mark a feature as completed"""
        feature = self._get_feature(feature_id)
        if not feature:
            raise ValueError(f"Feature {feature_id} not found")

        feature.status = FeatureStatus.COMPLETED
        feature.updated_at = datetime.utcnow()

        # Move to completed list
        self.backlog.remove(feature)
        self.completed.append(feature)

        self._save_backlog()
        self._save_completed()

    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        status_counts = {}
        for status in FeatureStatus:
            count = len([f for f in self.backlog if f.status == status])
            status_counts[status.value] = count

        return {
            'total_in_backlog': len(self.backlog),
            'total_completed': len(self.completed),
            'by_status': status_counts,
            'by_priority': {
                'critical': len([f for f in self.backlog if f.priority == FeaturePriority.CRITICAL]),
                'high': len([f for f in self.backlog if f.priority == FeaturePriority.HIGH]),
                'medium': len([f for f in self.backlog if f.priority == FeaturePriority.MEDIUM]),
                'low': len([f for f in self.backlog if f.priority == FeaturePriority.LOW]),
            }
        }


# CLI interface
def main():
    """CLI entry point for feature pipeline"""
    import argparse

    parser = argparse.ArgumentParser(
        description="BlackBox5 Feature Pipeline"
    )
    parser.add_argument(
        "command",
        choices=["propose", "list", "review", "implement", "stats"],
        help="Command to execute"
    )
    parser.add_argument("--name", type=str, help="Feature name")
    parser.add_argument("--description", type=str, help="Feature description")
    parser.add_argument("--source", type=str, help="Source type")
    parser.add_argument("--priority", type=str, help="Priority level")
    parser.add_argument("--feature-id", type=str, help="Feature ID")
    parser.add_argument("--blackbox", type=Path, default=Path.cwd(), help="BlackBox5 root")

    args = parser.parse_args()

    pipeline = FeaturePipeline(args.blackbox)

    if args.command == "propose":
        if not args.name or not args.description:
            parser.error("--name and --description required for propose")

        feature = pipeline.propose_feature(
            name=args.name,
            description=args.description,
            source_type=args.source or "internal",
            source_name="manual",
            priority=FeaturePriority(args.priority) if args.priority else FeaturePriority.MEDIUM
        )

        print(f"✅ Feature proposed: {feature.feature_id}")
        print(f"   Name: {feature.name}")

    elif args.command == "list":
        features = pipeline.get_backlog()
        print(f"\n📋 Feature Backlog ({len(features)} features)\n")

        for feature in features:
            print(f"   [{feature.feature_id}] {feature.name}")
            print(f"      Status: {feature.status.value} | Priority: {feature.priority.value}")
            print()

    elif args.command == "stats":
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


if __name__ == "__main__":
    main()
