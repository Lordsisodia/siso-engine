"""
Epic Agent - PRD to Technical Epic Transformation

This module transforms Product Requirements Documents (PRDs) into
technical Epics with architecture, components, and implementation strategy.
Uses first-principles thinking and systematic decision making.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .prd_agent import PRDData, PRDAgent
from .exceptions import EpicValidationError


class EpicStatus(Enum):
    """Epic status enumeration."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class TechnicalDecision:
    """A technical decision with options and rationale."""

    title: str
    options: List[Dict[str, Any]]
    chosen: str
    rationale: str
    impact: str


@dataclass
class Component:
    """A component specification."""

    name: str
    purpose: str
    file_location: str
    dependencies: List[str]
    required_by: List[str]
    interface: str
    acceptance_criteria: List[str]
    testing_strategy: Dict[str, str]


@dataclass
class ImplementationPhase:
    """An implementation phase."""

    name: str
    components: List[str]
    deliverables: List[str]
    success_criteria: List[str]


@dataclass
class EpicData:
    """Structured Epic data."""

    # Metadata
    title: str
    status: str
    prd_id: str
    prd_title: str
    created: str
    updated: str
    epic_id: str = ""

    # Overview
    overview: str = ""
    problem_statement: str = ""
    solution_overview: str = ""

    # First Principles Design
    essential_components: List[str] = field(default_factory=list)
    eliminated_components: List[Dict[str, str]] = field(default_factory=list)
    minimal_viable: List[str] = field(default_factory=list)

    # Technical Decisions
    technical_decisions: List[TechnicalDecision] = field(default_factory=list)

    # Implementation Strategy
    phases: List[ImplementationPhase] = field(default_factory=list)

    # Components
    components: List[Component] = field(default_factory=list)

    # Data Flow
    data_flow_description: List[str] = field(default_factory=list)
    data_structures: str = ""

    # Error Handling
    error_scenarios: List[Dict[str, str]] = field(default_factory=list)

    # Testing Strategy
    unit_tests: List[Dict[str, str]] = field(default_factory=list)
    integration_tests: List[Dict[str, str]] = field(default_factory=list)
    e2e_tests: List[Dict[str, str]] = field(default_factory=list)

    # Security & Performance
    security: Dict[str, str] = field(default_factory=dict)
    performance: Dict[str, str] = field(default_factory=dict)
    scalability: Dict[str, str] = field(default_factory=dict)

    # Dependencies
    skills_required: List[Dict[str, str]] = field(default_factory=list)
    agents_required: List[Dict[str, str]] = field(default_factory=list)
    external_dependencies: List[Dict[str, str]] = field(default_factory=list)
    system_dependencies: List[Dict[str, str]] = field(default_factory=list)

    # Rollout Plan
    rollout_phases: List[Dict[str, str]] = field(default_factory=list)

    # Monitoring
    metrics: List[str] = field(default_factory=list)
    alerts: List[Dict[str, str]] = field(default_factory=list)
    dashboards: List[Dict[str, str]] = field(default_factory=list)

    # Risks
    risks: List[Dict[str, Any]] = field(default_factory=list)

    # Open Questions
    open_questions: List[Dict[str, str]] = field(default_factory=list)


class TechnicalDecisionMaker:
    """
    Make technical decisions from first principles.

    Analyzes requirements and constraints to recommend technical approaches
    with clear options, rationale, and impact analysis.
    """

    def __init__(self):
        """Initialize technical decision maker."""
        pass

    def make_architecture_decision(
        self,
        prd: PRDData,
        context: Dict[str, Any]
    ) -> TechnicalDecision:
        """
        Decide on overall architecture approach.

        Args:
            prd: Source PRD data
            context: Additional context

        Returns:
            TechnicalDecision for architecture
        """
        # This is a placeholder - in production, this would use AI/LLM
        # to analyze the PRD and make recommendations

        options = [
            {
                "name": "Monolithic",
                "description": "Single unified codebase",
                "pros": ["Simpler deployment", "Easier debugging", "Lower complexity"],
                "cons": ["Harder to scale", "Tight coupling", "Single point of failure"]
            },
            {
                "name": "Modular Monolith",
                "description": "Modules within single deployment",
                "pros": ["Clear boundaries", "Easier to evolve", "Simple deployment"],
                "cons": ["Shared memory", "Module communication overhead"],
                "chosen": True
            },
            {
                "name": "Microservices",
                "description": "Independent service deployments",
                "pros": ["Independent scaling", "Technology diversity", "Fault isolation"],
                "cons": ["Network complexity", "Data consistency", "Operational overhead"]
            }
        ]

        return TechnicalDecision(
            title="Architecture Pattern",
            options=options,
            chosen="Modular Monolith",
            rationale="Based on first principles: we need clear boundaries for team autonomy "
                     "but don't yet have the scale to justify microservices complexity. "
                     "Modular monolith gives us structure without operational overhead.",
            impact="Enables independent module development while maintaining simple deployment. "
                  "Can evolve to microservices if needed."
        )

    def make_data_storage_decision(
        self,
        prd: PRDData,
        context: Dict[str, Any]
    ) -> TechnicalDecision:
        """
        Decide on data storage approach.

        Args:
            prd: Source PRD data
            context: Additional context

        Returns:
            TechnicalDecision for data storage
        """
        # Analyze requirements for data storage needs
        needs_realtime = any("real-time" in r["description"].lower() for r in prd.functional_requirements)
        needs_complex_queries = any("query" in r["description"].lower() for r in prd.functional_requirements)

        options = [
            {
                "name": "PostgreSQL",
                "description": "Relational database",
                "pros": ["ACID compliance", "Complex queries", "Mature ecosystem"],
                "cons": ["Vertical scaling", "Schema rigidity"],
                "chosen": True
            },
            {
                "name": "MongoDB",
                "description": "NoSQL document store",
                "pros": ["Flexible schema", "Horizontal scaling", "JSON-native"],
                "cons": ["No ACID", "Query limitations"]
            },
            {
                "name": "Redis",
                "description": "In-memory key-value store",
                "pros": ["Fast", "Simple data models"],
                "cons": ["Limited queries", "Memory constraints"]
            }
        ]

        return TechnicalDecision(
            title="Primary Data Storage",
            options=options,
            chosen="PostgreSQL",
            rationale="First principles: we need reliable data storage with complex query capabilities. "
                     "PostgreSQL provides ACID guarantees and mature tooling. "
                     f"{'Real-time requirements suggest caching layer may be needed.' if needs_realtime else ''}",
            impact="Enables complex queries and data relationships. "
                  "Can add Redis cache later if performance requires it."
        )


class ArchitectureGenerator:
    """
    Generate architecture from first principles.

    Creates minimal viable architecture based on fundamental truths
    and requirements, avoiding over-engineering.
    """

    def __init__(self):
        """Initialize architecture generator."""
        pass

    def generate_architecture(
        self,
        prd: PRDData,
        decisions: List[TechnicalDecision]
    ) -> Dict[str, Any]:
        """
        Generate minimal viable architecture.

        Args:
            prd: Source PRD data
            decisions: Technical decisions made

        Returns:
            Architecture specification
        """
        # Extract essential components from requirements
        essential = self._identify_essential_components(prd)

        # Identify what to eliminate
        eliminated = self._identify_unnecessary_components(prd, essential)

        # Define minimal viable implementation
        minimal_viable = self._define_minimal_viable(prd, essential)

        return {
            "essential_components": essential,
            "eliminated_components": eliminated,
            "minimal_viable_implementation": minimal_viable,
            "architecture_diagram": self._generate_diagram(essential)
        }

    def _identify_essential_components(self, prd: PRDData) -> List[str]:
        """Identify essential components from first principles."""
        components = []

        # Analyze functional requirements
        for req in prd.functional_requirements:
            # Extract component hints from requirements
            if "api" in req["description"].lower():
                components.append("API Layer")
            if "database" in req["description"].lower() or "persist" in req["description"].lower():
                components.append("Data Persistence Layer")
            if "auth" in req["description"].lower() or "security" in req["description"].lower():
                components.append("Authentication/Authorization")
            if "ui" in req["description"].lower() or "interface" in req["description"].lower():
                components.append("User Interface")

        # Add essential infrastructure
        essentials = list(set(components))

        # Always include these essentials
        if "Configuration Management" not in essentials:
            essentials.append("Configuration Management")
        if "Logging/Monitoring" not in essentials:
            essentials.append("Logging/Monitoring")

        return essentials

    def _identify_unnecessary_components(
        self,
        prd: PRDData,
        essential: List[str]
    ) -> List[Dict[str, str]]:
        """Identify components that are NOT needed (avoid over-engineering)."""
        eliminated = []

        # Check if we need caching
        if not any("performance" in r["description"].lower() or
                   "scale" in r["description"].lower()
                   for r in prd.functional_requirements):
            eliminated.append({
                "component": "Distributed Cache",
                "reason": "No high-performance or scaling requirements identified yet"
            })

        # Check if we need message queue
        if not any("async" in r["description"].lower() or
                   "background" in r["description"].lower()
                   for r in prd.functional_requirements):
            eliminated.append({
                "component": "Message Queue",
                "reason": "No asynchronous processing requirements"
            })

        # Check if we need search engine
        if not any("search" in r["description"].lower() or
                   "full-text" in r["description"].lower()
                   for r in prd.functional_requirements):
            eliminated.append({
                "component": "Elasticsearch/Solr",
                "reason": "No complex search requirements"
            })

        return eliminated

    def _define_minimal_viable(
        self,
        prd: PRDData,
        essential: List[str]
    ) -> List[str]:
        """Define minimal viable implementation features."""
        mvp = []

        # Extract core features from functional requirements
        for req in prd.functional_requirements[:5]:  # First 5 are usually core
            mvp.append(req["description"])

        return mvp

    def _generate_diagram(self, components: List[str]) -> str:
        """Generate simple architecture diagram."""
        diagram = "```\n"
        diagram += "[User Interface]\n"
        diagram += "       ↓\n"
        diagram += "[API Layer]\n"
        diagram += "       ↓\n"
        diagram += "[Business Logic]\n"
        diagram += "       ↓\n"
        diagram += "[Data Layer]\n"
        diagram += "```"
        return diagram


class ComponentBreakdown:
    """
    Break down architecture into implementable components.

    Creates detailed component specifications with:
    - File locations
    - Interfaces
    - Dependencies
    - Testing strategy
    """

    def __init__(self):
        """Initialize component breakdown."""
        pass

    def create_components(
        self,
        prd: PRDData,
        architecture: Dict[str, Any]
    ) -> List[Component]:
        """
        Create component specifications.

        Args:
            prd: Source PRD data
            architecture: Architecture specification

        Returns:
            List of Component objects
        """
        components = []

        # Create components from essential architecture
        essential = architecture.get("essential_components", [])

        for i, comp_name in enumerate(essential):
            component = self._create_component_spec(
                comp_name,
                prd,
                architecture
            )
            components.append(component)

        return components

    def _create_component_spec(
        self,
        name: str,
        prd: PRDData,
        architecture: Dict[str, Any]
    ) -> Component:
        """Create a single component specification."""

        # Determine file location based on component type
        file_location = self._get_file_location(name)

        # Determine dependencies
        dependencies = self._get_dependencies(name, architecture)

        # Determine what depends on this
        required_by = self._get_dependents(name, architecture)

        # Generate interface
        interface = self._generate_interface(name, prd)

        # Generate acceptance criteria
        acceptance_criteria = self._generate_acceptance_criteria(name, prd)

        # Generate testing strategy
        testing_strategy = self._generate_testing_strategy(name, prd)

        return Component(
            name=name,
            purpose=self._get_purpose(name, prd),
            file_location=file_location,
            dependencies=dependencies,
            required_by=required_by,
            interface=interface,
            acceptance_criteria=acceptance_criteria,
            testing_strategy=testing_strategy
        )

    def _get_file_location(self, component_name: str) -> str:
        """Determine file location for component."""
        locations = {
            "API Layer": "src/api/",
            "Data Persistence Layer": "src/data/",
            "Authentication/Authorization": "src/auth/",
            "User Interface": "src/ui/",
            "Configuration Management": "src/config/",
            "Logging/Monitoring": "src/observability/"
        }
        return locations.get(component_name, f"src/{component_name.lower().replace('/', '_')}/")

    def _get_dependencies(self, name: str, architecture: Dict[str, Any]) -> List[str]:
        """Get component dependencies."""
        dependencies_map = {
            "API Layer": ["Business Logic", "Authentication/Authorization"],
            "Data Persistence Layer": ["Configuration Management"],
            "Authentication/Authorization": ["Data Persistence Layer"],
            "User Interface": ["API Layer"],
            "Business Logic": ["Data Persistence Layer"]
        }
        return dependencies_map.get(name, [])

    def _get_dependents(self, name: str, architecture: Dict[str, Any]) -> List[str]:
        """Get what depends on this component."""
        dependents_map = {
            "API Layer": ["User Interface"],
            "Data Persistence Layer": ["Business Logic", "Authentication/Authorization"],
            "Authentication/Authorization": ["API Layer"],
            "User Interface": [],
            "Configuration Management": ["Data Persistence Layer"]
        }
        return dependents_map.get(name, [])

    def _get_purpose(self, name: str, prd: PRDData) -> str:
        """Get component purpose."""
        purposes = {
            "API Layer": "Expose REST/GraphQL endpoints for client communication",
            "Data Persistence Layer": "Manage data storage and retrieval with ACID guarantees",
            "Authentication/Authorization": "Verify identity and enforce access control",
            "User Interface": "Provide user interaction surface",
            "Configuration Management": "Centralize configuration management",
            "Logging/Monitoring": "Track system health and performance"
        }
        return purposes.get(name, f"Implement {name} functionality")

    def _generate_interface(self, name: str, prd: PRDData) -> str:
        """Generate component interface."""
        if name == "API Layer":
            return """```typescript
interface API {
  // Endpoints
  get(endpoint: string): Promise<Response>
  post(endpoint: string, data: any): Promise<Response>
  put(endpoint: string, data: any): Promise<Response>
  delete(endpoint: string): Promise<Response>
}
```"""
        elif name == "Data Persistence Layer":
            return """```typescript
interface DataRepository {
  // CRUD operations
  findById(id: string): Promise<Entity>
  findAll(filter: QueryFilter): Promise<Entity[]>
  create(entity: Entity): Promise<Entity>
  update(id: string, changes: Partial<Entity>): Promise<Entity>
  delete(id: string): Promise<boolean>
}
```"""
        else:
            return f"""```typescript
interface {name.replace('/', '')} {{
  // Component-specific methods
  // TODO: Define based on requirements
}}
```"""

    def _generate_acceptance_criteria(self, name: str, prd: PRDData) -> List[str]:
        """Generate acceptance criteria for component."""
        return [
            f"AC-1: {name} handles normal operations without errors",
            f"AC-2: {name} handles edge cases gracefully",
            f"AC-3: {name} meets performance requirements",
            f"AC-4: {name} is properly tested with unit and integration tests"
        ]

    def _generate_testing_strategy(self, name: str, prd: PRDData) -> Dict[str, str]:
        """Generate testing strategy for component."""
        return {
            "unit_test": f"Test {name} methods in isolation with mocked dependencies",
            "integration_test": f"Test {name} interactions with its dependencies",
            "edge_case": f"Test {name} behavior with invalid inputs and error conditions"
        }


class EpicParser:
    """
    Parse Epic markdown files into structured data.
    """

    def __init__(self, specs_root: Optional[Path] = None):
        """Initialize Epic parser."""
        self.specs_root = Path(specs_root) if specs_root else Path.cwd() / "specs" / "epics"

    def parse_file(self, epic_path: Path) -> EpicData:
        """
        Parse an Epic markdown file.

        Args:
            epic_path: Path to Epic markdown file

        Returns:
            EpicData object with parsed content
        """
        if not epic_path.exists():
            raise EpicValidationError(f"Epic file not found", epic_id=str(epic_path))

        content = epic_path.read_text()
        return self.parse_content(content, epic_path)

    def parse_content(self, content: str, source_path: Optional[Path] = None) -> EpicData:
        """
        Parse Epic content from markdown string.

        Args:
            content: Markdown content
            source_path: Optional source file path

        Returns:
            EpicData object with parsed content
        """
        # Extract metadata
        title_match = re.search(r'^#\s+Epic:\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Untitled Epic"

        status_match = re.search(r'\*\*Status\*\*:\s*(.+?)(?:\s*\||\n|$)', content)
        status = status_match.group(1).strip() if status_match else "Draft"

        prd_match = re.search(r'\*\*PRD\*\*:\s*(.+?)(?:\n|$)', content)
        prd_id = prd_match.group(1).strip() if prd_match else ""

        created_match = re.search(r'\*\*Created\*\*:\s*(.+?)(?:\n|$)', content)
        created = created_match.group(1).strip() if created_match else datetime.now().strftime("%Y-%m-%d")

        updated_match = re.search(r'\*\*Last Updated\*\*:\s*(.+?)(?:\n|$)', content)
        updated = updated_match.group(1).strip() if updated_match else created

        epic_id = source_path.stem if source_path else ""

        epic = EpicData(
            title=title,
            status=status,
            prd_id=prd_id,
            prd_title="",  # Would need to load PRD to get this
            created=created,
            updated=updated,
            epic_id=epic_id
        )

        # Extract sections
        epic.overview = self._extract_overview(content)
        epic.problem_statement = self._extract_section_text(content, "Problem Statement")
        epic.solution_overview = self._extract_section_text(content, "Solution Overview")
        epic.essential_components = self._extract_list(content, "Essential Components")
        epic.minimal_viable = self._extract_list(content, "Minimal Viable Implementation")
        epic.phases = self._extract_phases(content)
        epic.error_scenarios = self._extract_error_scenarios(content)
        epic.risks = self._extract_risks_table(content)
        epic.open_questions = self._extract_open_questions(content)

        return epic

    def _extract_overview(self, content: str) -> str:
        """Extract overview section."""
        pattern = r'##\s+Overview.*?\n(.*?)(?=##|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()[:500]
        return ""

    def _extract_section_text(self, content: str, section_title: str) -> str:
        """Extract a section's text content."""
        pattern = rf'\*\*{section_title}\*\*:\s*(.+?)(?=\n\n|\n\*\*|$)'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_list(self, content: str, list_title: str) -> List[str]:
        """Extract a list from content."""
        pattern = rf'\*\*{list_title}\*\*.*?\n(.*?)(?=\n\n|\n\*\*|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        items = []
        for line in match.group(1).split('\n'):
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')):
                item = re.sub(r'^\d+\.\s*|[-*]\s*', '', line)
                items.append(item.strip())

        return items

    def _extract_phases(self, content: str) -> List[ImplementationPhase]:
        """Extract implementation phases."""
        pattern = r'###\s+Phase\s+\d+:\s*(.+?)\n.*?\*\*Components\*\*:(.*?)\*\*Deliverables\*\*:(.*?)\*\*Success Criteria\*\*:(.*?)(?=###\s+Phase|$)'
        phases = []

        for match in re.finditer(pattern, content, re.DOTALL):
            name = match.group(1).strip()
            components = [c.strip() for c in match.group(2).split('-') if c.strip()][1:]
            deliverables = [d.strip() for d in match.group(3).split('-') if d.strip()][1:]
            criteria = [c.strip() for c in match.group(4).split('-') if c.strip()][1:]

            phases.append(ImplementationPhase(
                name=name,
                components=components,
                deliverables=deliverables,
                success_criteria=criteria
            ))

        return phases

    def _extract_error_scenarios(self, content: str) -> List[Dict[str, str]]:
        """Extract error handling scenarios."""
        scenarios = []

        pattern = r'###\s+Error Scenario\s+\d+:\s*(.+?)\n.*?\*\*Response\*\*:(.*?)(?=###\s+Error|##|\Z)'
        for match in re.finditer(pattern, content, re.DOTALL):
            scenario_name = match.group(1).strip()
            response_text = match.group(2).strip()

            scenario = {"name": scenario_name}

            # Extract response details
            error_msg = re.search(r'\*\*Error message\*\*:\s*(.+?)(?=\n|$)', response_text)
            if error_msg:
                scenario["error_message"] = error_msg.group(1).strip()

            system_action = re.search(r'\*\*System action\*\*:\s*(.+?)(?=\n|$)', response_text)
            if system_action:
                scenario["system_action"] = system_action.group(1).strip()

            recovery = re.search(r'\*\*Recovery\*\*:\s*(.+?)(?=\n|$)', response_text)
            if recovery:
                scenario["recovery"] = recovery.group(1).strip()

            scenarios.append(scenario)

        return scenarios

    def _extract_risks_table(self, content: str) -> List[Dict[str, Any]]:
        """Extract risks from table format."""
        risks = []

        # Find risks section
        pattern = r'##\s+Risks & Mitigation.*?\n(.*?)(?=##|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return risks

        section = match.group(1)

        # Parse table rows (skip header)
        for line in section.split('\n'):
            if line.startswith('|') and 'Risk' not in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 4:
                    risks.append({
                        "risk": parts[0],
                        "likelihood": parts[1],
                        "impact": parts[2],
                        "mitigation": parts[3],
                        "owner": parts[4] if len(parts) > 4 else "TBD"
                    })

        return risks

    def _extract_open_questions(self, content: str) -> List[Dict[str, str]]:
        """Extract open questions."""
        questions = []

        pattern = r'##\s+Open Questions.*?\n(.*?)(?=##|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return questions

        for line in match.group(1).split('\n'):
            if line.startswith('- ['):
                parts = re.split(r'\]:\s*', line[3:], 1)
                if len(parts) == 2:
                    questions.append({
                        "question": parts[0].strip(),
                        "importance": parts[1].strip()
                    })

        return questions


class EpicValidator:
    """
    Validate Epic completeness and quality.

    Checks for:
    - Alignment with PRD
    - Complete technical decisions
    - Component specifications
    - Testing strategy
    - Implementation phases
    """

    def __init__(self):
        """Initialize Epic validator."""
        pass

    def validate(self, epic: EpicData, prd: Optional[PRDData] = None) -> Dict[str, Any]:
        """
        Validate an Epic.

        Args:
            epic: EpicData to validate
            prd: Optional source PRD for alignment check

        Returns:
            Validation results
        """
        errors = []
        warnings = []

        # Check required fields
        if not epic.title or epic.title == "Untitled Epic":
            errors.append("Epic must have a title")

        if not epic.prd_id:
            warnings.append("Epic has no linked PRD")

        # Check technical decisions
        if len(epic.technical_decisions) == 0:
            errors.append("No technical decisions documented")

        # Check components
        if len(epic.components) == 0:
            errors.append("No components specified")

        # Check implementation phases
        if len(epic.phases) == 0:
            errors.append("No implementation phases defined")

        # Check testing strategy
        if len(epic.unit_tests) == 0 and len(epic.integration_tests) == 0:
            warnings.append("Testing strategy incomplete")

        # Check error handling
        if len(epic.error_scenarios) == 0:
            warnings.append("No error scenarios defined")

        # Check monitoring
        if len(epic.metrics) == 0:
            warnings.append("No monitoring metrics defined")

        # Check PRD alignment if PRD provided
        if prd:
            alignment_errors = self._check_prd_alignment(epic, prd)
            errors.extend(alignment_errors)

        valid = len(errors) == 0

        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "completion_percent": self._calculate_completion(epic)
        }

    def _check_prd_alignment(self, epic: EpicData, prd: PRDData) -> List[str]:
        """Check that Epic aligns with PRD."""
        errors = []

        # Check that all functional requirements are addressed
        # (This is a simplified check - real implementation would be more sophisticated)

        return errors

    def _calculate_completion(self, epic: EpicData) -> float:
        """Calculate Epic completion percentage."""
        fields = [
            epic.title,
            epic.overview,
            epic.essential_components,
            epic.technical_decisions,
            epic.components,
            epic.phases,
            epic.unit_tests,
            epic.security
        ]

        completed = sum(1 for f in fields if f)
        return (completed / len(fields)) * 100


class EpicAgent:
    """
    Main Epic management agent.

    Transforms PRDs into technical Epics with:
    - First-principles architecture
    - Technical decisions with rationale
    - Component breakdown
    - Implementation strategy
    - Testing approach
    """

    def __init__(
        self,
        specs_root: Optional[Path] = None,
        prd_agent: Optional[PRDAgent] = None
    ):
        """
        Initialize Epic agent.

        Args:
            specs_root: Root directory for spec files
            prd_agent: Optional PRDAgent instance
        """
        self.specs_root = Path(specs_root) if specs_root else Path.cwd() / "specs"
        self.epics_root = self.specs_root / "epics"
        self.prds_root = self.specs_root / "prds"

        self.prd_agent = prd_agent or PRDAgent(self.prds_root)
        self.parser = EpicParser(self.epics_root)
        self.validator = EpicValidator()
        self.decision_maker = TechnicalDecisionMaker()
        self.architecture_generator = ArchitectureGenerator()
        self.component_breakdown = ComponentBreakdown()

    def create_epic(
        self,
        prd_id: str,
        title: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> EpicData:
        """
        Create an Epic from a PRD.

        Args:
            prd_id: PRD identifier
            title: Optional epic title (defaults to PRD title)
            output_path: Optional output file path

        Returns:
            Created EpicData object

        Raises:
            EpicValidationError: If creation fails
        """
        # Load PRD
        prd = self.prd_agent.load_prd(prd_id)

        # Create epic data structure
        epic = EpicData(
            title=title or f"Epic: {prd.title}",
            status=EpicStatus.DRAFT.value,
            prd_id=prd.prd_id,
            prd_title=prd.title,
            created=datetime.now().strftime("%Y-%m-%d"),
            updated=datetime.now().strftime("%Y-%m-%d"),
            epic_id=self._generate_epic_id(prd.prd_id)
        )

        # Transform PRD to Epic
        epic = self._transform_prd_to_epic(prd, epic)

        # Generate markdown
        if output_path is None:
            output_path = self.epics_root / f"{epic.epic_id}.md"

        self._write_epic_markdown(epic, output_path)

        print(f"Created Epic: {epic.epic_id} at {output_path}")

        return epic

    def _transform_prd_to_epic(self, prd: PRDData, epic: EpicData) -> EpicData:
        """Transform PRD data into Epic data."""

        # Overview
        epic.overview = f"{prd.title}\n\nOne-sentence summary: Implement {prd.title.lower()}"
        epic.problem_statement = prd.problem.get("what_problem_are_we_trying_to_solve", "")

        # Generate architecture
        decisions = [
            self.decision_maker.make_architecture_decision(prd, {}),
            self.decision_maker.make_data_storage_decision(prd, {})
        ]

        architecture = self.architecture_generator.generate_architecture(prd, decisions)
        epic.technical_decisions = decisions
        epic.essential_components = architecture["essential_components"]
        epic.eliminated_components = architecture["eliminated_components"]
        epic.minimal_viable = architecture["minimal_viable_implementation"]

        # Generate components
        components = self.component_breakdown.create_components(prd, architecture)
        epic.components = components

        # Generate implementation phases
        epic.phases = self._generate_phases(components)

        # Generate testing strategy
        epic.unit_tests = self._generate_unit_tests(components)
        epic.integration_tests = self._generate_integration_tests(components)

        # Copy risks from PRD
        epic.risks = prd.risks

        # Copy open questions from PRD
        epic.open_questions = prd.open_questions

        # Generate security, performance, scalability
        epic.security = self._generate_security_specs(prd)
        epic.performance = self._generate_performance_specs(prd)
        epic.scalability = self._generate_scalability_specs(prd)

        return epic

    def _generate_epic_id(self, prd_id: str) -> str:
        """Generate epic ID from PRD ID."""
        # Remove PRD- prefix if present, add EPIC- prefix
        base_id = prd_id.replace("PRD-", "").replace("prd-", "")
        return f"EPIC-{base_id}"

    def _generate_phases(self, components: List[Component]) -> List[ImplementationPhase]:
        """Generate implementation phases from components."""

        # Divide components into phases
        total = len(components)
        phase_size = max(1, total // 3)

        phases = []

        # Phase 1: Foundation
        phase1_components = [c.name for c in components[:phase_size]]
        phases.append(ImplementationPhase(
            name="Phase 1: Foundation",
            components=phase1_components,
            deliverables=[f"Implement {c}" for c in phase1_components],
            success_criteria=["All foundation components pass tests", "CI/CD pipeline operational"]
        ))

        # Phase 2: Core Features
        phase2_components = [c.name for c in components[phase_size:phase_size*2]]
        phases.append(ImplementationPhase(
            name="Phase 2: Core Features",
            components=phase2_components,
            deliverables=[f"Implement {c}" for c in phase2_components],
            success_criteria=["All core features functional", "Integration tests passing"]
        ))

        # Phase 3: Polish & Optimize
        phase3_components = [c.name for c in components[phase_size*2:]]
        phases.append(ImplementationPhase(
            name="Phase 3: Polish & Optimize",
            components=phase3_components,
            deliverables=[f"Implement {c}" for c in phase3_components] + ["Performance optimization", "Documentation"],
            success_criteria=["Performance targets met", "Documentation complete", "Ready for release"]
        ))

        return phases

    def _generate_unit_tests(self, components: List[Component]) -> List[Dict[str, str]]:
        """Generate unit test specifications."""
        tests = []

        for component in components:
            tests.append({
                "name": f"{component.name} unit tests",
                "input": "Various inputs",
                "expected": "Expected outputs",
                "covers": f"{component.name} methods and logic"
            })

        return tests

    def _generate_integration_tests(self, components: List[Component]) -> List[Dict[str, str]]:
        """Generate integration test specifications."""
        tests = []

        # Test component interactions
        for i in range(len(components) - 1):
            tests.append({
                "name": f"{components[i].name} → {components[i+1].name} integration",
                "components": f"{components[i].name}, {components[i+1].name}",
                "scenario": f"Test data flow between {components[i].name} and {components[i+1].name}",
                "expected": "Data flows correctly, errors handled"
            })

        return tests

    def _generate_security_specs(self, prd: PRDData) -> Dict[str, str]:
        """Generate security specifications."""
        return {
            "authentication": "Implement JWT-based authentication",
            "authorization": "Role-based access control (RBAC)",
            "data_protection": "Encrypt sensitive data at rest and in transit",
            "input_validation": "Validate and sanitize all user inputs"
        }

    def _generate_performance_specs(self, prd: PRDData) -> Dict[str, str]:
        """Generate performance specifications."""
        return {
            "response_time": "< 100ms for API calls",
            "throughput": "1000 req/s minimum",
            "resource_usage": "< 512MB RAM per instance",
            "caching": "Cache frequently accessed data"
        }

    def _generate_scalability_specs(self, prd: PRDData) -> Dict[str, str]:
        """Generate scalability specifications."""
        return {
            "horizontal_scaling": "Stateless design enables horizontal scaling",
            "vertical_scaling": "Can increase resources as needed",
            "bottlenecks": "Database connection pooling, API rate limiting"
        }

    def _write_epic_markdown(self, epic: EpicData, output_path: Path) -> None:
        """Write epic to markdown file."""

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            # Header
            f.write(f"# Epic: {epic.title}\n\n")
            f.write(f"> **Status**: {epic.status} | **PRD**: {epic.prd_id}\n")
            f.write(f"> **Created**: {epic.created} | **Last Updated**: {epic.updated}\n\n")

            # Overview
            f.write("## Overview\n\n")
            f.write(f"{epic.overview}\n\n")
            f.write(f"**Traces to PRD**: {epic.prd_id} - {epic.prd_title}\n\n")
            f.write(f"**Problem Statement**: {epic.problem_statement}\n\n")
            f.write(f"**Solution Overview**: {epic.solution_overview}\n\n")

            # First Principles Design
            f.write("## First Principles Design\n\n")
            f.write("### Core Architecture\n\n")
            f.write("**Essential Components** (what we MUST have):\n")
            for i, comp in enumerate(epic.essential_components, 1):
                f.write(f"{i}. {comp}\n")
            f.write("\n")

            if epic.eliminated_components:
                f.write("**What to Eliminate** (not needed):\n")
                for elim in epic.eliminated_components:
                    f.write(f"- [{elim['component']}] - {elim['reason']}\n")
                f.write("\n")

            f.write("**Minimal Viable Implementation**:\n")
            for item in epic.minimal_viable:
                f.write(f"- {item}\n")
            f.write("\n")

            # Technical Decisions
            f.write("### Key Technical Decisions\n\n")
            for i, decision in enumerate(epic.technical_decisions, 1):
                f.write(f"#### Decision {i}: {decision.title}\n")
                f.write("**Options Considered**:\n")
                for option in decision.options:
                    chosen = " ✅ **CHOSEN**" if option.get("chosen") else ""
                    f.write(f"- Option: {option['name']}{chosen}\n")
                    if option.get("pros"):
                        f.write(f"  - Pros: {', '.join(option['pros'])}\n")
                    if option.get("cons"):
                        f.write(f"  - Cons: {', '.join(option['cons'])}\n")
                f.write(f"\n**Rationale**: {decision.rationale}\n\n")
                f.write(f"**Impact**: {decision.impact}\n\n")
                f.write("---\n\n")

            # Implementation Strategy
            f.write("## Implementation Strategy\n\n")
            for phase in epic.phases:
                f.write(f"### {phase.name}\n")
                f.write("**Components**:\n")
                for comp in phase.components:
                    f.write(f"- {comp}\n")
                f.write("\n**Deliverables**:\n")
                for deliverable in phase.deliverables:
                    f.write(f"- [ ] {deliverable}\n")
                f.write("\n**Success Criteria**:\n")
                for criterion in phase.success_criteria:
                    f.write(f"- [ ] {criterion}\n")
                f.write("\n---\n\n")

            # Components
            f.write("## Component Specifications\n\n")
            for component in epic.components:
                f.write(f"### Component: {component.name}\n\n")
                f.write(f"**Purpose**: {component.purpose}\n\n")
                f.write(f"**File Location**: `{component.file_location}`\n\n")
                f.write(f"**Dependencies**: {', '.join(component.dependencies) if component.dependencies else 'None'}\n\n")
                f.write(f"**Required By**: {', '.join(component.required_by) if component.required_by else 'None'}\n\n")
                f.write("**Interface**:\n")
                f.write(f"{component.interface}\n\n")
                f.write("**Acceptance Criteria**:\n")
                for ac in component.acceptance_criteria:
                    f.write(f"- [ ] {ac}\n")
                f.write("\n**Testing Strategy**:\n")
                for test_type, test_desc in component.testing_strategy.items():
                    f.write(f"- {test_type}: {test_desc}\n")
                f.write("\n---\n\n")

            # Security & Performance
            f.write("## Security & Performance\n\n")
            f.write("### Security\n")
            for key, value in epic.security.items():
                f.write(f"- **{key}**: {value}\n")
            f.write("\n### Performance\n")
            for key, value in epic.performance.items():
                f.write(f"- **{key}**: {value}\n")
            f.write("\n### Scalability\n")
            for key, value in epic.scalability.items():
                f.write(f"- **{key}**: {value}\n")
            f.write("\n")

            # Testing Strategy
            f.write("## Testing Strategy\n\n")
            f.write("### Unit Tests\n")
            for test in epic.unit_tests:
                f.write(f"- **{test['name']}**\n")
                f.write(f"  - Covers: {test['covers']}\n")
            f.write("\n### Integration Tests\n")
            for test in epic.integration_tests:
                f.write(f"- **{test['name']}**\n")
                f.write(f"  - Components: {test['components']}\n")
                f.write(f"  - Scenario: {test['scenario']}\n")
            f.write("\n")

            # Risks
            if epic.risks:
                f.write("## Risks & Mitigation\n\n")
                f.write("| Risk | Likelihood | Impact | Mitigation |\n")
                f.write("|------|------------|--------|------------|\n")
                for risk in epic.risks:
                    f.write(f"| {risk.get('risk', '')} | {risk.get('likelihood', '')} | {risk.get('impact', '')} | {risk.get('mitigation', '')} |\n")
                f.write("\n")

            # Open Questions
            if epic.open_questions:
                f.write("## Open Questions\n\n")
                for question in epic.open_questions:
                    f.write(f"- [ ] [{question['question']}]: {question['importance']}\n")
                f.write("\n")

    def load_epic(self, epic_id: str) -> EpicData:
        """
        Load an Epic by ID.

        Args:
            epic_id: Epic identifier

        Returns:
            EpicData object
        """
        epic_path = self.epics_root / f"{epic_id}.md"

        if not epic_path.exists():
            raise EpicValidationError(f"Epic not found: {epic_id}", epic_id=epic_id)

        return self.parser.parse_file(epic_path)

    def validate_epic(self, epic_id: str) -> Dict[str, Any]:
        """
        Validate an Epic.

        Args:
            epic_id: Epic identifier

        Returns:
            Validation results
        """
        epic = self.load_epic(epic_id)

        # Load PRD for alignment check
        prd = None
        if epic.prd_id:
            try:
                prd = self.prd_agent.load_prd(epic.prd_id)
            except Exception:
                pass

        return self.validator.validate(epic, prd)

    def list_epics(self, status: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List all Epics.

        Args:
            status: Optional status filter

        Returns:
            List of Epic info dictionaries
        """
        epics = []

        for epic_file in self.epics_root.glob("*.md"):
            if epic_file.name == "TEMPLATE.md":
                continue

            try:
                epic = self.parser.parse_file(epic_file)

                if status is None or epic.status.lower() == status.lower():
                    epics.append({
                        "id": epic.epic_id,
                        "title": epic.title,
                        "status": epic.status,
                        "prd_id": epic.prd_id,
                        "created": epic.created
                    })
            except Exception as e:
                print(f"Warning: Could not parse {epic_file}: {e}")

        return sorted(epics, key=lambda x: x["created"], reverse=True)

    def get_epic_summary(self, epic_id: str) -> Dict[str, Any]:
        """
        Get a summary of an Epic.

        Args:
            epic_id: Epic identifier

        Returns:
            Epic summary dictionary
        """
        epic = self.load_epic(epic_id)

        return {
            "id": epic.epic_id,
            "title": epic.title,
            "status": epic.status,
            "prd_id": epic.prd_id,
            "prd_title": epic.prd_title,
            "created": epic.created,
            "updated": epic.updated,
            "components_count": len(epic.components),
            "phases_count": len(epic.phases),
            "decisions_count": len(epic.technical_decisions),
            "risks_count": len(epic.risks),
            "open_questions_count": len(epic.open_questions)
        }
