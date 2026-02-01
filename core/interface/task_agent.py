"""
Task Agent for BlackBox5 Spec-Driven Development Pipeline

Handles Epic → Tasks decomposition with acceptance criteria generation,
complexity estimation, and dependency analysis.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from .prd_agent import PRDData
from .epic_agent import EpicData, TechnicalDecision
from .config import TaskConfig
from .exceptions import TaskValidationError, TaskCreationError


class TaskType(Enum):
    """Types of tasks in the pipeline"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    TEST = "test"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplexityLevel(Enum):
    """Task complexity levels"""
    TRIVIAL = "trivial"  # < 1 hour
    SIMPLE = "simple"     # 1-2 hours
    MODERATE = "moderate"  # 2-4 hours
    COMPLEX = "complex"    # 4-8 hours
    VERY_COMPLEX = "very_complex"  # 8+ hours


@dataclass
class AcceptanceCriterion:
    """Single acceptance criterion for a task"""
    criterion_id: str
    description: str
    verification_method: str  # "automated_test", "manual_test", "code_review", "checklist"
    priority: str = "required"  # "required", "optional", "stretch"

    def to_markdown(self) -> str:
        """Convert to markdown format"""
        icon = "✅" if self.priority == "required" else "🔹" if self.priority == "optional" else "⭐"
        return f"{icon} **{self.criterion_id}**: {self.description}\n   *Verification: {self.verification_method}*"


@dataclass
class TaskDependency:
    """Dependency on another task or resource"""
    dependency_id: str
    type: str  # "task", "epic", "external", "resource"
    description: str
    blocking: bool = True

    def to_markdown(self) -> str:
        """Convert to markdown format"""
        icon = "🚫" if self.blocking else "🔗"
        return f"{icon} **{self.type.upper()}**: {self.description} ({self.dependency_id})"


@dataclass
class TaskEstimate:
    """Time and complexity estimate for a task"""
    hours_low: float
    hours_high: float
    hours_expected: float
    complexity: ComplexityLevel
    confidence: float  # 0.0 to 1.0

    def to_markdown(self) -> str:
        """Convert to markdown format"""
        return f"""**Estimate**:
- Complexity: {self.complexity.value.title()}
- Expected: {self.hours_expected}h
- Range: {self.hours_low}h - {self.hours_high}h
- Confidence: {self.confidence:.0%}"""


@dataclass
class Task:
    """A single task in the development pipeline"""
    task_id: str
    title: str
    description: str
    task_type: TaskType
    priority: TaskPriority
    status: str = "todo"  # todo, in_progress, in_review, done, blocked

    # Task breakdown
    acceptance_criteria: List[AcceptanceCriterion] = field(default_factory=list)
    dependencies: List[TaskDependency] = field(default_factory=list)
    estimate: Optional[TaskEstimate] = None

    # Technical details
    technical_notes: List[str] = field(default_factory=list)
    files_to_modify: List[str] = field(default_factory=list)
    tests_required: bool = True

    # Metadata
    epic_id: Optional[str] = None
    prd_id: Optional[str] = None
    assignee: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        """Convert task to markdown format"""
        md = f"""# {self.task_id}: {self.title}

**Type**: {self.task_type.value.title()} | **Priority**: {self.priority.value.title()} | **Status**: {self.status.replace('_', ' ').title()}

## Description

{self.description}

"""

        if self.estimate:
            md += f"## Estimates\n\n{self.estimate.to_markdown()}\n\n"

        if self.acceptance_criteria:
            md += "## Acceptance Criteria\n\n"
            for criterion in self.acceptance_criteria:
                md += f"{criterion.to_markdown()}\n\n"
            md += "\n"

        if self.dependencies:
            md += "## Dependencies\n\n"
            for dep in self.dependencies:
                md += f"{dep.to_markdown()}\n"
            md += "\n"

        if self.technical_notes:
            md += "## Technical Notes\n\n"
            for note in self.technical_notes:
                md += f"- {note}\n"
            md += "\n"

        if self.files_to_modify:
            md += "## Expected File Changes\n\n"
            for file_path in self.files_to_modify:
                md += f"- `{file_path}`\n"
            md += "\n"

        if self.labels:
            md += f"## Labels\n\n{', '.join(f'`{label}`' for label in self.labels)}\n\n"

        if self.epic_id or self.prd_id:
            md += "## Traceability\n\n"
            if self.prd_id:
                md += f"- **PRD**: {self.prd_id}\n"
            if self.epic_id:
                md += f"- **Epic**: {self.epic_id}\n"
            md += "\n"

        md += f"---\n*Created: {self.created_at}*"

        return md

    @classmethod
    def from_markdown(cls, content: str, epic_id: Optional[str] = None, prd_id: Optional[str] = None) -> 'Task':
        """Parse task from markdown format"""
        lines = content.split('\n')

        # Extract task ID and title
        title_match = re.match(r'#\s+([A-Z]+-\d+):\s*(.+)', lines[0])
        if not title_match:
            raise TaskValidationError("Invalid task format: missing task ID and title")

        task_id = title_match.group(1)
        title = title_match.group(2)

        # Parse metadata
        task_type = TaskType.FEATURE
        priority = TaskPriority.MEDIUM
        description = ""
        acceptance_criteria = []
        dependencies = []
        technical_notes = []
        files_to_modify = []
        labels = []

        current_section = None
        current_criterion = []

        for line in lines[1:]:
            if line.startswith('## '):
                current_section = line[3:].lower().strip()
                continue

            if not current_section:
                # Parse metadata line
                if '**Type**:' in line:
                    type_match = re.search(r'\*\*Type\*\*:\s*(\w+)', line)
                    if type_match:
                        task_type = TaskType(type_match.group(1).lower())
                if '**Priority**:' in line:
                    priority_match = re.search(r'\*\*Priority\*\*:\s*(\w+)', line)
                    if priority_match:
                        priority = TaskPriority(priority_match.group(1).lower())
                continue

            if current_section == 'description':
                description += line + '\n'

            elif current_section == 'acceptance criteria':
                if line.startswith('✅') or line.startswith('🔹') or line.startswith('⭐'):
                    if current_criterion:
                        acceptance_criteria.append(AcceptanceCriterion(
                            criterion_id=f"AC-{len(acceptance_criteria) + 1}",
                            description=current_criterion[0],
                            verification_method="manual_test"
                        ))
                    current_criterion = [line.lstrip('✅🔹⭐ ').strip()]
                elif current_criterion:
                    current_criterion.append(line.strip())

            elif current_section == 'dependencies':
                if line.startswith('🚫') or line.startswith('🔗'):
                    dep_type = 'TASK' if 'TASK' in line else 'EPIC' if 'EPIC' in line else 'EXTERNAL'
                    dep_desc = line.split(':', 1)[1].strip() if ':' in line else line
                    dep_id = re.search(r'\(([A-Z]+-\d+)\)', dep_desc)
                    dependencies.append(TaskDependency(
                        dependency_id=dep_id.group(1) if dep_id else f"DEP-{len(dependencies) + 1}",
                        type=dep_type.lower(),
                        description=dep_desc.split('(')[0].strip(),
                        blocking=line.startswith('🚫')
                    ))

            elif current_section == 'technical notes':
                if line.startswith('-'):
                    technical_notes.append(line[1:].strip())

            elif current_section == 'expected file changes':
                if line.startswith('-'):
                    file_match = re.search(r'`([^`]+)`', line)
                    if file_match:
                        files_to_modify.append(file_match.group(1))

            elif current_section == 'labels':
                labels = re.findall(r'`([^`]+)`', line)

        # Add last criterion
        if current_criterion:
            acceptance_criteria.append(AcceptanceCriterion(
                criterion_id=f"AC-{len(acceptance_criteria) + 1}",
                description=current_criterion[0],
                verification_method="manual_test"
            ))

        return cls(
            task_id=task_id,
            title=title,
            description=description.strip(),
            task_type=task_type,
            priority=priority,
            acceptance_criteria=acceptance_criteria,
            dependencies=dependencies,
            technical_notes=technical_notes,
            files_to_modify=files_to_modify,
            labels=labels,
            epic_id=epic_id,
            prd_id=prd_id
        )


@dataclass
class TaskDocument:
    """Container for all tasks derived from an epic"""
    epic_id: str
    epic_title: str
    tasks: List[Task]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        """Convert task document to markdown"""
        md = f"""# Tasks for Epic: {self.epic_id}

**Epic Title**: {self.epic_title}

*Generated: {self.created_at}*

---

"""

        for task in self.tasks:
            md += task.to_markdown()
            md += "\n\n---\n\n"

        # Add summary section
        md += f"""## Task Summary

**Total Tasks**: {len(self.tasks)}

**By Status**:
"""
        status_counts = {}
        for task in self.tasks:
            status_counts[task.status] = status_counts.get(task.status, 0) + 1

        for status, count in sorted(status_counts.items()):
            md += f"- {status.replace('_', ' ').title()}: {count}\n"

        md += f"""
**By Priority**:
"""
        priority_counts = {}
        for task in self.tasks:
            priority_counts[task.priority.value] = priority_counts.get(task.priority.value, 0) + 1

        for priority, count in sorted(priority_counts.items()):
            md += f"- {priority.title()}: {count}\n"

        md += f"""
**By Type**:
"""
        type_counts = {}
        for task in self.tasks:
            type_counts[task.task_type.value] = type_counts.get(task.task_type.value, 0) + 1

        for task_type, count in sorted(type_counts.items()):
            md += f"- {task_type.title()}: {count}\n"

        md += f"""
**Total Estimated Hours**: {sum(t.estimate.hours_expected for t in self.tasks if t.estimate):.1f}h

"""

        return md


class ComplexityEstimator:
    """Estimate task complexity based on various factors"""

    COMPLEXITY_KEYWORDS = {
        ComplexityLevel.TRIVIAL: [
            'update', 'rename', 'simple', 'basic', 'minor', 'tweak', 'adjust'
        ],
        ComplexityLevel.SIMPLE: [
            'add', 'create', 'implement', 'basic', 'standard', 'routine'
        ],
        ComplexityLevel.MODERATE: [
            'refactor', 'improve', 'enhance', 'modify', 'extend', 'integrate'
        ],
        ComplexityLevel.COMPLEX: [
            'redesign', 'restructure', 'optimize', 'migrate', 'transform'
        ],
        ComplexityLevel.VERY_COMPLEX: [
            'rebuild', 'rewrite', 'architectural', 'system-wide', 'migration'
        ]
    }

    def estimate(self, task: Task, technical_decisions: List[TechnicalDecision]) -> TaskEstimate:
        """Estimate complexity and time for a task"""

        # Base complexity from title/description
        text = (task.title + ' ' + task.description).lower()
        base_complexity = self._analyze_text_complexity(text)

        # Adjust based on technical decisions
        complexity_modifier = self._analyze_technical_impact(task, technical_decisions)

        # Adjust based on dependencies
        dependency_modifier = 1.0 + (len(task.dependencies) * 0.1)

        # Adjust based on files to modify
        file_modifier = 1.0 + (len(task.files_to_modify) * 0.05)

        # Calculate final complexity
        if complexity_modifier > 1.5:
            base_complexity = ComplexityLevel(max(base_complexity.value + 1, 4))
        elif complexity_modifier < 0.7:
            base_complexity = ComplexityLevel(min(base_complexity.value - 1, 0))

        # Calculate hours based on complexity
        hours_map = {
            ComplexityLevel.TRIVIAL: (0.5, 1.0),
            ComplexityLevel.SIMPLE: (1.0, 2.0),
            ComplexityLevel.MODERATE: (2.0, 4.0),
            ComplexityLevel.COMPLEX: (4.0, 8.0),
            ComplexityLevel.VERY_COMPLEX: (8.0, 16.0)
        }

        hours_low, hours_high = hours_map[base_complexity]
        hours_low *= dependency_modifier * file_modifier
        hours_high *= dependency_modifier * file_modifier
        hours_expected = (hours_low + hours_high) / 2

        # Confidence decreases with complexity
        complexity_index = list(ComplexityLevel).index(base_complexity)
        confidence = max(0.5, 0.95 - (complexity_index * 0.1))

        return TaskEstimate(
            hours_low=round(hours_low, 1),
            hours_high=round(hours_high, 1),
            hours_expected=round(hours_expected, 1),
            complexity=base_complexity,
            confidence=round(confidence, 2)
        )

    def _analyze_text_complexity(self, text: str) -> ComplexityLevel:
        """Analyze text to determine base complexity"""
        scores = {complexity: 0 for complexity in ComplexityLevel}

        for complexity, keywords in self.COMPLEXITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[complexity] += 1

        # Return complexity with highest score
        return max(scores.items(), key=lambda x: x[1])[0]

    def _analyze_technical_impact(self, task: Task, decisions: List[TechnicalDecision]) -> float:
        """Analyze technical decisions impact on task complexity"""
        modifier = 1.0

        for decision in decisions:
            if decision.chosen.lower() in task.title.lower() + task.description.lower():
                if 'complex' in decision.rationale.lower() or 'challenging' in decision.rationale.lower():
                    modifier += 0.3
                elif 'simple' in decision.rationale.lower() or 'straightforward' in decision.rationale.lower():
                    modifier -= 0.2

        return min(2.0, max(0.5, modifier))


class DependencyAnalyzer:
    """Analyze and create dependencies between tasks"""

    def analyze(self, tasks: List[Task]) -> List[Task]:
        """Analyze task dependencies and add them to tasks"""
        enriched_tasks = []

        for i, task in enumerate(tasks):
            # Find dependencies based on file overlap
            for j, other_task in enumerate(tasks):
                if i >= j:  # Don't compare with self or already compared
                    continue

                # Check file overlap
                task_files = set(task.files_to_modify)
                other_files = set(other_task.files_to_modify)

                if task_files & other_files:  # Overlap exists
                    # Earlier task should block later task
                    if i < j:
                        task.dependencies.append(TaskDependency(
                            dependency_id=other_task.task_id,
                            type="task",
                            description=f"Requires completion of {other_task.title}",
                            blocking=True
                        ))

            enriched_tasks.append(task)

        return enriched_tasks


class AcceptanceCriteriaGenerator:
    """Generate acceptance criteria for tasks"""

    TEMPLATES = {
        TaskType.FEATURE: [
            "Feature functions as expected in {context}",
            "Edge cases are handled appropriately",
            "User feedback is clear and actionable",
            "Performance meets requirements"
        ],
        TaskType.BUGFIX: [
            "Bug is resolved and no longer reproducible",
            "Regression tests prevent future occurrences",
            "Root cause has been addressed",
            "Related issues are investigated"
        ],
        TaskType.REFACTOR: [
            "Code is more maintainable and readable",
            "Existing functionality is preserved",
            "Tests pass without modification",
            "Performance is not degraded"
        ],
        TaskType.TEST: [
            "Coverage is increased for {context}",
            "Tests are deterministic and reliable",
            "Edge cases are covered",
            "Tests document expected behavior"
        ],
        TaskType.PERFORMANCE: [
            "Performance improvement is measurable",
            "Bottlenecks are identified and addressed",
            "System stability is maintained",
            "Performance regression tests are in place"
        ]
    }

    def generate(self, task: Task, context: Dict[str, Any]) -> List[AcceptanceCriterion]:
        """Generate acceptance criteria for a task"""
        criteria = []

        templates = self.TEMPLATES.get(task.task_type, self.TEMPLATES[TaskType.FEATURE])

        for i, template in enumerate(templates):
            criterion = template.format(
                context=task.title.lower(),
                **context
            )

            criteria.append(AcceptanceCriterion(
                criterion_id=f"AC-{i + 1}",
                description=criterion,
                verification_method="automated_test" if task.tests_required else "manual_test",
                priority="required" if i < 2 else "optional"
            ))

        return criteria


class TaskAgent:
    """Main agent for task creation and management"""

    def __init__(self, config: Optional[TaskConfig] = None):
        self.config = config or TaskConfig()
        self.complexity_estimator = ComplexityEstimator()
        self.dependency_analyzer = DependencyAnalyzer()
        self.criteria_generator = AcceptanceCriteriaGenerator()

    def create_tasks(self, epic: EpicData, prd: Optional[PRDData] = None) -> TaskDocument:
        """Create tasks from an epic document"""

        tasks = []

        # Generate tasks from epic components
        for component in epic.components:
            component_tasks = self._create_component_tasks(component, epic, prd)
            tasks.extend(component_tasks)

        # Generate tasks from technical decisions
        for decision in epic.technical_decisions:
            decision_tasks = self._create_decision_tasks(decision, epic, prd)
            tasks.extend(decision_tasks)

        # Enrich tasks with dependencies
        tasks = self.dependency_analyzer.analyze(tasks)

        # Create task document
        task_doc = TaskDocument(
            epic_id=epic.epic_id,
            epic_title=epic.title,
            tasks=tasks,
            metadata={
                "total_estimated_hours": sum(t.estimate.hours_expected for t in tasks if t.estimate),
                "generated_from": f"epic:{epic.epic_id}",
                "prd_reference": prd.prd_id if prd else None
            }
        )

        return task_doc

    def _create_component_tasks(self, component: Dict, epic: EpicData, prd: Optional[PRDData]) -> List[Task]:
        """Create tasks from an epic component"""
        tasks = []

        # Implementation task
        impl_task = Task(
            task_id=f"{epic.epic_id}-{len(tasks) + 1:03d}",
            title=f"Implement {component.get('name', 'Component')}",
            description=f"""Implement the {component.get('name', 'component')} as specified in the epic.

**Component Overview**:
{component.get('description', 'No description available')}

**Responsibilities**:
""" + "\n".join(f"- {resp}" for resp in component.get('responsibilities', [])),

            task_type=TaskType.FEATURE,
            priority=self._determine_priority(component, epic),
            files_to_modify=component.get('proposed_files', []),
            technical_notes=[
                f"Part of epic: {epic.title}",
                f"Component: {component.get('name', 'Unknown')}"
            ],
            epic_id=epic.epic_id,
            prd_id=prd.prd_id if prd else None,
            labels=[epic.epic_id.lower(), "feature", "implementation"]
        )

        # Generate acceptance criteria
        impl_task.acceptance_criteria = self.criteria_generator.generate(
            impl_task,
            {"component": component.get('name', 'component')}
        )

        # Estimate complexity
        impl_task.estimate = self.complexity_estimator.estimate(
            impl_task,
            epic.technical_decisions
        )

        tasks.append(impl_task)

        # Testing task
        test_task = Task(
            task_id=f"{epic.epic_id}-{len(tasks) + 1:03d}",
            title=f"Add tests for {component.get('name', 'Component')}",
            description=f"""Create comprehensive tests for {component.get('name', 'component')}.

Tests should cover:
- Happy path scenarios
- Edge cases
- Error conditions
- Performance characteristics
""",
            task_type=TaskType.TEST,
            priority=self._determine_priority(component, epic),
            files_to_modify=[
                f.replace('.ts', '.test.ts')
                for f in component.get('proposed_files', [])
                if f.endswith('.ts')
            ],
            technical_notes=[
                f"Testing for: {component.get('name', 'Component')}",
                "Ensure test coverage > 80%"
            ],
            epic_id=epic.epic_id,
            prd_id=prd.prd_id if prd else None,
            labels=[epic.epic_id.lower(), "testing", "quality"]
        )

        test_task.acceptance_criteria = self.criteria_generator.generate(
            test_task,
            {"component": component.get('name', 'component')}
        )

        test_task.estimate = self.complexity_estimator.estimate(
            test_task,
            epic.technical_decisions
        )

        # Test task depends on implementation
        test_task.dependencies.append(TaskDependency(
            dependency_id=impl_task.task_id,
            type="task",
            description=f"Requires {impl_task.title}",
            blocking=True
        ))

        tasks.append(test_task)

        return tasks

    def _create_decision_tasks(self, decision: Any, epic: EpicData, prd: Optional[PRDData]) -> List[Task]:
        """Create tasks from technical decisions"""
        tasks = []

        # Skip if decision is straightforward
        if 'simple' in decision.rationale.lower() or 'standard' in decision.rationale.lower():
            return tasks

        task = Task(
            task_id=f"{epic.epic_id}-{len(tasks) + 100:03d}",
            title=f"Implement {decision.chosen}",
            description=f"""Implement technical decision: {decision.title}

**Decision**: {decision.chosen}

**Rationale**:
{decision.rationale}

**Options Considered**:
""" + "\n".join(f"- {opt}" for opt in decision.options),

            task_type=TaskType.FEATURE,
            priority=TaskPriority.HIGH if 'critical' in decision.rationale.lower() else TaskPriority.MEDIUM,
            technical_notes=[
                f"Technical decision: {decision.title}",
                decision.rationale
            ],
            epic_id=epic.epic_id,
            prd_id=prd.prd_id if prd else None,
            labels=[epic.epic_id.lower(), "technical-decision", "implementation"]
        )

        task.acceptance_criteria = self.criteria_generator.generate(
            task,
            {"decision": decision.chosen}
        )

        task.estimate = self.complexity_estimator.estimate(
            task,
            [decision]
        )

        tasks.append(task)

        return tasks

    def _determine_priority(self, component: Dict, epic: EpicData) -> TaskPriority:
        """Determine task priority based on component and epic"""
        # Check for explicit priority indicators
        text = component.get('description', '') + ' ' + str(component.get('responsibilities', ''))

        if any(word in text.lower() for word in ['critical', 'urgent', 'security', 'blocking']):
            return TaskPriority.CRITICAL
        elif any(word in text.lower() for word in ['important', 'priority', 'key']):
            return TaskPriority.HIGH
        elif any(word in text.lower() for word in ['nice to have', 'future', 'enhancement']):
            return TaskPriority.LOW
        else:
            return TaskPriority.MEDIUM

    def validate_task(self, task: Task) -> List[str]:
        """Validate a task and return list of issues"""
        issues = []

        if not task.title:
            issues.append("Task title is required")

        if not task.description:
            issues.append("Task description is required")

        if not task.acceptance_criteria:
            issues.append("Task must have at least one acceptance criterion")

        if not task.estimate:
            issues.append("Task must have an estimate")

        # Validate acceptance criteria
        for i, criterion in enumerate(task.acceptance_criteria):
            if not criterion.description:
                issues.append(f"Acceptance criterion {i + 1} is missing description")

        return issues

    def parse_task_file(self, task_file: Path) -> Task:
        """Parse a task from a markdown file"""
        if not task_file.exists():
            raise TaskCreationError(f"Task file not found: {task_file}")

        content = task_file.read_text()
        return Task.from_markdown(content)

    def save_task_document(self, task_doc: TaskDocument, output_dir: Path) -> Path:
        """Save task document to file"""
        output_dir = Path(output_dir)

        # Create tasks subdirectory
        tasks_dir = output_dir / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)

        # Save combined task document
        output_file = tasks_dir / f"{task_doc.epic_id.lower()}-tasks.md"
        output_file.write_text(task_doc.to_markdown())

        # Save individual tasks
        for task in task_doc.tasks:
            task_file = tasks_dir / f"{task.task_id.lower()}.md"
            task_file.write_text(task.to_markdown())

        return output_file

    def list_tasks(self, tasks_dir: Path, epic_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available tasks, optionally filtered by epic"""
        tasks_dir = Path(tasks_dir)

        if not tasks_dir.exists():
            return []

        tasks = []

        for task_file in tasks_dir.glob("*-tasks.md"):
            if epic_id and not task_file.stem.startswith(epic_id.lower()):
                continue

            try:
                task_doc = self.parse_task_document(task_file)
                tasks.append({
                    "epic_id": task_doc.epic_id,
                    "epic_title": task_doc.epic_title,
                    "task_count": len(task_doc.tasks),
                    "file": str(task_file)
                })
            except TaskValidationError:
                # Expected validation error - skip invalid documents silently
                continue
            except Exception as e:
                # Log unexpected errors for debugging while continuing processing
                import warnings
                warnings.warn(f"Unexpected error parsing task document {task_file}: {e}")
                continue

        return tasks

    def parse_task_document(self, task_file: Path) -> TaskDocument:
        """Parse a task document from file"""
        content = task_file.read_text()

        # Extract epic info
        epic_match = re.search(r'# Tasks for Epic: ([A-Z]+-\d+)', content)
        if not epic_match:
            raise TaskValidationError("Invalid task document format")

        epic_id = epic_match.group(1)

        title_match = re.search(r'\*\*Epic Title\*\*:\s*(.+)', content)
        epic_title = title_match.group(1) if title_match else "Unknown Epic"

        # Parse individual tasks
        tasks = []
        task_blocks = re.split(r'\n---\n', content)

        for block in task_blocks:
            if block.strip().startswith('# '):
                try:
                    task = Task.from_markdown(block.strip(), epic_id=epic_id)
                    tasks.append(task)
                except TaskValidationError:
                    # Skip invalid task blocks silently
                    continue
                except Exception as e:
                    # Log unexpected errors for debugging
                    import warnings
                    warnings.warn(f"Unexpected error parsing task block in {task_file}: {e}")
                    continue

        return TaskDocument(
            epic_id=epic_id,
            epic_title=epic_title,
            tasks=tasks
        )


# Convenience functions for CLI
def create_tasks_from_epic(epic_file: Path, output_dir: Path, prd_file: Optional[Path] = None) -> Path:
    """Create tasks from an epic file - convenience function for CLI"""
    agent = TaskAgent()

    # Parse epic
    from .epic_agent import EpicAgent
    epic_agent = EpicAgent()
    epic = epic_agent.parse_epic(epic_file)

    # Parse PRD if provided
    prd = None
    if prd_file and prd_file.exists():
        prd_agent = PRDAgent()
        prd = prd_agent.parse_prd(prd_file)

    # Create tasks
    task_doc = agent.create_tasks(epic, prd)

    # Save
    return agent.save_task_document(task_doc, output_dir)
