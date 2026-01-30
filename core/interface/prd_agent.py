"""
PRD Agent - Product Requirements Document Management

This module provides the PRD parsing and validation capabilities
needed to transform PRDs into technical epics.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

from .exceptions import PRDValidationError


@dataclass
class PRDData:
    """Structured PRD data extracted from markdown files."""

    # Metadata
    title: str
    status: str
    created: str
    author: str = ""
    prd_id: str = ""

    # First Principles Analysis
    problem: Dict[str, Any] = field(default_factory=dict)
    truths: Dict[str, Any] = field(default_factory=dict)
    solution: Dict[str, Any] = field(default_factory=dict)

    # Requirements
    functional_requirements: List[Dict[str, str]] = field(default_factory=list)
    non_functional_requirements: List[Dict[str, str]] = field(default_factory=list)
    out_of_scope: List[str] = field(default_factory=list)

    # Success Metrics
    success_metrics: Dict[str, List[str]] = field(default_factory=dict)

    # User Stories
    user_stories: List[str] = field(default_factory=list)

    # Acceptance Criteria
    acceptance_criteria: List[str] = field(default_factory=list)

    # Related Work
    dependencies: List[str] = field(default_factory=list)
    required_for: List[str] = field(default_factory=list)
    similar_work: List[Dict[str, str]] = field(default_factory=list)
    conflicts: List[Dict[str, str]] = field(default_factory=list)

    # Risks
    risks: List[Dict[str, Any]] = field(default_factory=list)

    # Open Questions
    open_questions: List[Dict[str, str]] = field(default_factory=list)

    # Technical Constraints
    technical_constraints: List[str] = field(default_factory=list)


class PRDParser:
    """
    Parse PRD markdown files into structured data.

    Extracts all sections from the PRD template including:
    - First principles analysis
    - Requirements (functional & non-functional)
    - Success metrics
    - User stories
    - Acceptance criteria
    - Risks and dependencies
    """

    def __init__(self, specs_root: Optional[Path] = None):
        """
        Initialize PRD parser.

        Args:
            specs_root: Root directory for PRD files
        """
        self.specs_root = Path(specs_root) if specs_root else Path.cwd() / "specs" / "prds"

    def parse_file(self, prd_path: Path) -> PRDData:
        """
        Parse a PRD markdown file.

        Args:
            prd_path: Path to PRD markdown file

        Returns:
            PRDData object with parsed content

        Raises:
            PRDValidationError: If file is invalid or missing required sections
        """
        if not prd_path.exists():
            raise PRDValidationError(f"PRD file not found", field="file", value=prd_path)

        content = prd_path.read_text()
        return self.parse_content(content, prd_path)

    def parse_content(self, content: str, source_path: Optional[Path] = None) -> PRDData:
        """
        Parse PRD content from markdown string.

        Args:
            content: Markdown content
            source_path: Optional source file path

        Returns:
            PRDData object with parsed content
        """
        # Extract header metadata
        title_match = re.search(r'^#\s+PRD:\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Untitled PRD"

        status_match = re.search(r'\*\*Status\*\*:\s*(.+?)(?:\n|$)', content)
        status = status_match.group(1).strip() if status_match else "Draft"

        created_match = re.search(r'\*\*Created\*\*:\s*(.+?)(?:\n|$)', content)
        created = created_match.group(1).strip() if created_match else datetime.now().strftime("%Y-%m-%d")

        author_match = re.search(r'\*\*Author\*\*:\s*(.+?)(?:\n|$)', content)
        author = author_match.group(1).strip() if author_match else ""

        prd_id = source_path.stem if source_path else ""

        # Create PRD data structure
        prd = PRDData(
            title=title,
            status=status,
            created=created,
            author=author,
            prd_id=prd_id
        )

        # Extract sections
        prd.problem = self._extract_section(content, "The Problem")
        prd.truths = self._extract_truths(content)
        prd.solution = self._extract_section(content, "Solution from First Principles")
        prd.functional_requirements = self._extract_requirements(content, "Functional Requirements")
        prd.non_functional_requirements = self._extract_requirements(content, "Non-Functional Requirements")
        prd.out_of_scope = self._extract_list_items(content, "Out of Scope")
        prd.success_metrics = self._extract_metrics(content)
        prd.user_stories = self._extract_user_stories(content)
        prd.acceptance_criteria = self._extract_list_items(content, "Acceptance Criteria")
        prd.dependencies = self._extract_related_list(content, "Dependencies", "Depends on")
        prd.required_for = self._extract_related_list(content, "Dependencies", "Required for")
        prd.similar_work = self._extract_similar_work(content)
        prd.conflicts = self._extract_conflicts(content)
        prd.risks = self._extract_risks(content)
        prd.open_questions = self._extract_questions(content)
        prd.technical_constraints = self._extract_technical_constraints(content)

        return prd

    def _extract_section(self, content: str, section_title: str) -> Dict[str, Any]:
        """Extract a section by title."""
        pattern = rf"##\s+{section_title}.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return {}

        section_content = match.group(1).strip()

        # Try to extract subsections
        subsections = {}
        subsection_matches = re.findall(r'\*\*(.+?)\*\*:\s*(.*?)(?=\n-|\n\*\*|$)', section_content, re.DOTALL)

        for key, value in subsection_matches:
            subsections[key.lower().replace(" ", "_")] = value.strip()

        return subsections

    def _extract_truths(self, content: str) -> Dict[str, Any]:
        """Extract fundamental truths and assumptions."""
        pattern = r"##\s+Fundamental Truths.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return {}

        section_content = match.group(1)

        truths = {
            "fundamental_truths": [],
            "assumptions": [],
            "real_constraints": [],
            "imagined_constraints": []
        }

        # Extract fundamental truths
        truths_match = re.search(r'\*\*What do we know to be TRUE\?\*\*(.*?)(?=\n\*\*|$)', section_content, re.DOTALL)
        if truths_match:
            truths["fundamental_truths"] = [
                line.strip().lstrip('- ')
                for line in truths_match.group(1).split('\n')
                if line.strip() and not line.strip().startswith('**')
            ]

        # Extract assumptions
        assumptions_match = re.search(r'\*\*What are our ASSUMPTIONS\?\*\*(.*?)(?=\n\*\*|$)', section_content, re.DOTALL)
        if assumptions_match:
            truths["assumptions"] = [
                line.strip().lstrip('- ')
                for line in assumptions_match.group(1).split('\n')
                if line.strip() and not line.strip().startswith('**')
            ]

        return truths

    def _extract_requirements(self, content: str, section_title: str) -> List[Dict[str, str]]:
        """Extract functional or non-functional requirements."""
        pattern = rf"##\s+{section_title}.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        section_content = match.group(1)
        requirements = []

        # Extract requirement items (format: - **FR-1**: Requirement)
        req_matches = re.findall(r'- \*\*([A-Z]+-\d+)\*:\*:\s*(.+?)(?=\n-|\n\n|$)', section_content, re.DOTALL)

        for req_id, req_text in req_matches:
            requirements.append({
                "id": req_id,
                "description": req_text.strip()
            })

        return requirements

    def _extract_list_items(self, content: str, section_title: str) -> List[str]:
        """Extract simple list items from a section."""
        pattern = rf"##\s+{section_title}.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        section_content = match.group(1)
        items = []

        # Extract list items
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                # Remove checkbox if present
                item = re.sub(r'^\[[ x]\]\s*', '', line[2:])
                items.append(item.strip())

        return items

    def _extract_metrics(self, content: str) -> Dict[str, List[str]]:
        """Extract success metrics."""
        pattern = r"##\s+Success Metrics.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return {}

        section_content = match.group(1)
        metrics = {"quantitative": [], "qualitative": []}

        # Extract quantitative metrics
        quant_match = re.search(r'\*\*Quantitative Metrics\*\*.*?\n(.*?)(?=\n\*\*|$)', section_content, re.DOTALL)
        if quant_match:
            for line in quant_match.group(1).split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    metrics["quantitative"].append(line[2:].strip())

        # Extract qualitative metrics
        qual_match = re.search(r'\*\*Qualitative Metrics\*\*.*?\n(.*?)(?=\n\*|$)', section_content, re.DOTALL)
        if qual_match:
            for line in qual_match.group(1).split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    metrics["qualitative"].append(line[2:].strip())

        return metrics

    def _extract_user_stories(self, content: str) -> List[str]:
        """Extract user stories."""
        pattern = r"##\s+User Stories.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        section_content = match.group(1)
        stories = []

        # Extract story items
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('- **Story') or line.startswith('- '):
                stories.append(re.sub(r'^- \*\*Story \d+:\*\*\s*', '', line))

        return [s.strip().lstrip('* ') for s in stories if s.strip()]

    def _extract_related_list(self, content: str, section: str, subsection: str) -> List[str]:
        """Extract related dependencies."""
        pattern = rf"##\s+{section}.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        section_content = match.group(1)
        pattern2 = rf'\*\*{subsection}\*\*:\s*(.+?)(?=\n|$)'

        matches = re.findall(pattern2, section_content)
        return [m.strip() for m in matches if m.strip()]

    def _extract_similar_work(self, content: str) -> List[Dict[str, str]]:
        """Extract similar skills/agents."""
        pattern = r"##\s+Related Work.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        section_content = match.group(1)
        similar = []

        # Extract similar work items (format: - [Similar skill 1]: How it differs)
        for line in section_content.split('\n'):
            line = line.strip()
            if '- **Similar' in line or '- [' in line:
                parts = re.split(r'\]:\s*', line[2:], 1)
                if len(parts) == 2:
                    similar.append({
                        "name": parts[0].lstrip('* ').strip(),
                        "difference": parts[1].strip()
                    })

        return similar

    def _extract_conflicts(self, content: str) -> List[Dict[str, str]]:
        """Extract conflicts and resolutions."""
        pattern = r"##\s+Related Work.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        section_content = match.group(1)
        conflicts = []

        # Look for conflicts subsection
        conflicts_match = re.search(r'###\s+Conflicts.*?\n(.*?)(?=##|\Z)', section_content, re.DOTALL)
        if conflicts_match:
            for line in conflicts_match.group(1).split('\n'):
                line = line.strip()
                if line.startswith('- ['):
                    parts = re.split(r'\]:\s*', line[3:], 1)
                    if len(parts) == 2:
                        conflicts.append({
                            "conflict": parts[0].strip(),
                            "resolution": parts[1].strip()
                        })

        return conflicts

    def _extract_risks(self, content: str) -> List[Dict[str, Any]]:
        """Extract risks and mitigations."""
        pattern = r"##\s+Risks & Mitigation.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        section_content = match.group(1)
        risks = []

        # Extract table rows (skip header)
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('|') and not line.startswith('| Risk'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 4:
                    risks.append({
                        "risk": parts[0],
                        "likelihood": parts[1],
                        "impact": parts[2],
                        "mitigation": parts[3]
                    })

        return risks

    def _extract_questions(self, content: str) -> List[Dict[str, str]]:
        """Extract open questions."""
        pattern = r"##\s+Open Questions.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        section_content = match.group(1)
        questions = []

        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('- ['):
                parts = re.split(r'\]:\s*', line[3:], 1)
                if len(parts) == 2:
                    questions.append({
                        "question": parts[0].strip(),
                        "importance": parts[1].strip()
                    })

        return questions

    def _extract_technical_constraints(self, content: str) -> List[str]:
        """Extract technical constraints from appendix."""
        pattern = r"##\s+Appendix.*?\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []

        section_content = match.group(1)
        constraints = []

        # Look for technical constraints subsection
        tc_match = re.search(r'###\s+Technical Constraints.*?\n(.*?)(?=###|$)', section_content, re.DOTALL)
        if tc_match:
            for line in tc_match.group(1).split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    constraints.append(line[2:].strip())

        return constraints


class PRDValidator:
    """
    Validate PRD completeness and quality.

    Checks for:
    - Required sections present
    - First principles analysis complete
    - Requirements are specific and testable
    - Success metrics defined
    - Acceptance criteria clear
    """

    def __init__(self):
        """Initialize PRD validator."""
        self.required_sections = [
            "The Problem",
            "Fundamental Truths",
            "Solution from First Principles",
            "Functional Requirements",
            "Success Metrics",
            "User Stories",
            "Acceptance Criteria"
        ]

    def validate(self, prd: PRDData) -> Dict[str, Any]:
        """
        Validate a PRD.

        Args:
            prd: PRDData object to validate

        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []

        # Check required fields
        if not prd.title or prd.title == "Untitled PRD":
            errors.append("PRD must have a title")

        # Check problem statement
        if not prd.problem.get("what_problem_are_we_trying_to_solve"):
            errors.append("Problem statement is incomplete")

        # Check fundamental truths
        if not prd.truths.get("fundamental_truths"):
            errors.append("No fundamental truths defined")

        # Check functional requirements
        if len(prd.functional_requirements) == 0:
            errors.append("No functional requirements defined")

        # Check success metrics
        if not prd.success_metrics.get("quantitative") and not prd.success_metrics.get("qualitative"):
            errors.append("No success metrics defined")

        # Check user stories
        if len(prd.user_stories) == 0:
            warnings.append("No user stories defined")

        # Check acceptance criteria
        if len(prd.acceptance_criteria) == 0:
            errors.append("No acceptance criteria defined")

        # Validate requirements quality
        for req in prd.functional_requirements:
            if len(req["description"]) < 10:
                warnings.append(f"Requirement {req['id']} may be too vague")

        # Validate acceptance criteria
        for i, criteria in enumerate(prd.acceptance_criteria):
            if not any(word in criteria.lower() for word in ["when", "then", "given", "should", "must"]):
                warnings.append(f"Acceptance criteria {i+1} may not be testable")

        valid = len(errors) == 0

        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "completion_percent": self._calculate_completion(prd)
        }

    def _calculate_completion(self, prd: PRDData) -> float:
        """Calculate PRD completion percentage."""
        fields = [
            prd.title,
            prd.problem,
            prd.truths.get("fundamental_truths"),
            prd.solution,
            prd.functional_requirements,
            prd.success_metrics,
            prd.user_stories,
            prd.acceptance_criteria
        ]

        completed = sum(1 for f in fields if f)
        return (completed / len(fields)) * 100


class PRDAgent:
    """
    Main PRD management agent.

    Provides high-level PRD operations including:
    - Creating PRDs from templates
    - Parsing PRD files
    - Validating PRD quality
    - Managing PRD workflow
    """

    def __init__(self, specs_root: Optional[Path] = None):
        """
        Initialize PRD agent.

        Args:
            specs_root: Root directory for PRD files
        """
        self.specs_root = Path(specs_root) if specs_root else Path.cwd() / "specs" / "prds"
        self.parser = PRDParser(self.specs_root)
        self.validator = PRDValidator()

    def load_prd(self, prd_id: str) -> PRDData:
        """
        Load a PRD by ID.

        Args:
            prd_id: PRD identifier (filename without extension)

        Returns:
            PRDData object

        Raises:
            PRDValidationError: If PRD not found or invalid
        """
        prd_path = self.specs_root / f"{prd_id}.md"

        if not prd_path.exists():
            # Try with PRD- prefix
            prd_path = self.specs_root / f"PRD-{prd_id}.md"

        if not prd_path.exists():
            raise PRDValidationError(f"PRD not found: {prd_id}", field="prd_id", value=prd_id)

        return self.parser.parse_file(prd_path)

    def validate_prd(self, prd_id: str) -> Dict[str, Any]:
        """
        Validate a PRD.

        Args:
            prd_id: PRD identifier

        Returns:
            Validation results
        """
        prd = self.load_prd(prd_id)
        return self.validator.validate(prd)

    def list_prds(self, status: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List all PRDs.

        Args:
            status: Optional status filter

        Returns:
            List of PRD info dictionaries
        """
        prds = []

        for prd_file in self.specs_root.glob("*.md"):
            if prd_file.name == "TEMPLATE.md":
                continue

            try:
                prd = self.parser.parse_file(prd_file)

                if status is None or prd.status.lower() == status.lower():
                    prds.append({
                        "id": prd_file.stem,
                        "title": prd.title,
                        "status": prd.status,
                        "created": prd.created
                    })
            except Exception as e:
                print(f"Warning: Could not parse {prd_file}: {e}")

        return sorted(prds, key=lambda x: x["created"], reverse=True)

    def get_prd_summary(self, prd_id: str) -> Dict[str, Any]:
        """
        Get a summary of a PRD.

        Args:
            prd_id: PRD identifier

        Returns:
            PRD summary dictionary
        """
        prd = self.load_prd(prd_id)

        return {
            "id": prd.prd_id,
            "title": prd.title,
            "status": prd.status,
            "created": prd.created,
            "author": prd.author,
            "problem": prd.problem.get("what_problem_are_we_trying_to_solve", "")[:200] + "...",
            "functional_requirements_count": len(prd.functional_requirements),
            "user_stories_count": len(prd.user_stories),
            "acceptance_criteria_count": len(prd.acceptance_criteria),
            "risks_count": len(prd.risks)
        }
