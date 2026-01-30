"""
STATE.md Management - Human-Readable Workflow Progress

This module provides the STATE.md management system for BlackBox5, which creates
and maintains a human-readable markdown file tracking workflow progress. This enables:
- Easy progress tracking for humans
- Simple workflow resumption
- Clear visualization of completed, in-progress, and pending tasks
- Integration with git for commit tracking
- Thread-safe file operations with locking
- Automatic backups before writes
- Markdown validation
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import re
import fcntl
import errno
import time
from contextlib import contextmanager
import shutil

logger = logging.getLogger(__name__)


@dataclass
class TaskState:
    """State of a single task"""
    task_id: str
    description: str
    status: str  # pending, in_progress, completed, failed
    wave_id: int
    files_modified: List[str] = field(default_factory=list)
    commit_hash: Optional[str] = None
    error: Optional[str] = None

    def to_markdown(self) -> str:
        """Convert task state to markdown line"""
        checkbox = {
            'completed': '[x]',
            'in_progress': '[~]',
            'pending': '[ ]',
            'failed': '[ ]'
        }.get(self.status, '[ ]')

        lines = [f"- {checkbox} **{self.task_id}**: {self.description}"]

        if self.commit_hash:
            lines.append(f"  - Commit: `{self.commit_hash}`")

        if self.files_modified:
            files_str = ', '.join(self.files_modified[:3])  # Show first 3
            if len(self.files_modified) > 3:
                files_str += f" (+{len(self.files_modified) - 3} more)"
            lines.append(f"  - Files: {files_str}")

        if self.error:
            lines.append(f"  - Error: {self.error}")

        return '\n'.join(lines)


@dataclass
class WorkflowState:
    """Complete workflow state from STATE.md"""
    workflow_id: str
    workflow_name: str
    current_wave: int
    total_waves: int
    tasks: Dict[str, TaskState]
    started_at: datetime
    updated_at: datetime
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Convert workflow state to STATE.md markdown format"""

        lines = [
            f"# Workflow: {self.workflow_name}",
            f"",
            f"**Workflow ID:** `{self.workflow_id}`",
            f"**Status:** Wave {self.current_wave}/{self.total_waves}",
            f"**Started:** {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Updated:** {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"---",
            f"",
        ]

        # Add progress bar
        if self.total_waves > 0:
            progress = self.current_wave / self.total_waves
            filled = int(progress * 20)
            bar = '█' * filled + '░' * (20 - filled)
            pct = int(progress * 100)
            lines.append(f"**Progress:** `{bar}` {pct}%")
            lines.append("")

        # Group tasks by status
        completed_tasks = [t for t in self.tasks.values() if t.status == 'completed']
        in_progress_tasks = [t for t in self.tasks.values() if t.status == 'in_progress']
        pending_tasks = [t for t in self.tasks.values() if t.status == 'pending']
        failed_tasks = [t for t in self.tasks.values() if t.status == 'failed']

        if completed_tasks:
            lines.append(f"## ✅ Completed ({len(completed_tasks)} tasks)")
            lines.append("")
            # Group by wave
            by_wave = {}
            for task in completed_tasks:
                if task.wave_id not in by_wave:
                    by_wave[task.wave_id] = []
                by_wave[task.wave_id].append(task)

            for wave_id in sorted(by_wave.keys()):
                # Add wave header if there are multiple waves with tasks
                if len(by_wave) > 1:
                    lines.append(f"### Wave {wave_id}")
                for task in by_wave[wave_id]:
                    lines.append(task.to_markdown())
                    lines.append("")
            lines.append("")

        if in_progress_tasks:
            lines.append(f"## 🔄 In Progress ({len(in_progress_tasks)} tasks)")
            lines.append("")
            for task in in_progress_tasks:
                lines.append(task.to_markdown())
                lines.append("")
            lines.append("")

        if pending_tasks:
            lines.append(f"## 📋 Pending ({len(pending_tasks)} tasks)")
            lines.append("")
            # Group by wave
            by_wave = {}
            for task in pending_tasks:
                if task.wave_id not in by_wave:
                    by_wave[task.wave_id] = []
                by_wave[task.wave_id].append(task)

            for wave_id in sorted(by_wave.keys()):
                if wave_id <= self.current_wave:
                    continue  # Skip pending tasks in current/past waves
                lines.append(f"### Wave {wave_id}")
                for task in by_wave[wave_id]:
                    lines.append(f"- [ ] **{task.task_id}**: {task.description}")
                lines.append("")
            lines.append("")

        if failed_tasks:
            lines.append(f"## ❌ Failed ({len(failed_tasks)} tasks)")
            lines.append("")
            for task in failed_tasks:
                lines.append(task.to_markdown())
                lines.append("")
            lines.append("")

        if self.notes:
            lines.append("## Notes")
            lines.append("")
            for note in self.notes:
                lines.append(f"- {note}")
            lines.append("")

        if self.metadata:
            lines.append("## Metadata")
            lines.append("")
            for key, value in self.metadata.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")

        return '\n'.join(lines)


class StateManager:
    """
    Manages STATE.md file for human-readable workflow progress.

    STATE.md format:
    # Workflow: {name}

    **Status:** Wave 2/4
    **Progress:** ████████░░░░░░░░░░░░ 40%

    ## ✅ Completed (Wave 1)
    - [x] Task 1: Description
      - Commit: abc123

    ## 🔄 In Progress (Wave 2)
    - [~] Task 4: Description

    ## 📋 Pending (Waves 3-4)
    ### Wave 3
    - [ ] Task 6: Description

    Features:
    - Thread-safe file locking (fcntl on Unix)
    - Automatic backups before writes
    - Markdown validation
    - Retry logic with exponential backoff
    """

    def __init__(self, state_path: Optional[Path] = None, max_retries: int = 3, retry_delay: float = 0.5):
        """
        Initialize state manager.

        Args:
            state_path: Path to STATE.md file (default: ./STATE.md)
            max_retries: Maximum number of retries for acquiring lock
            retry_delay: Initial retry delay in seconds (doubles each retry)
        """
        self.state_path = state_path or Path("STATE.md")
        self._lock_file = self.state_path.with_suffix('.lock')
        self._backup_path = self.state_path.with_suffix('.backup')
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    @contextmanager
    def _lock_state(self):
        """
        Acquire exclusive lock on STATE.md using fcntl.

        Raises:
            RuntimeError: If lock cannot be acquired after retries
        """
        # Ensure lock file directory exists
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)

        # Open lock file
        lock_file = open(self._lock_file, 'w')

        try:
            # Try to acquire exclusive lock (non-blocking)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.debug(f"Acquired lock on {self.state_path}")
            yield lock_file

        except IOError as e:
            if e.errno == errno.EWOULDBLOCK:
                raise RuntimeError(
                    f"STATE.md is locked by another process. "
                    f"If stale, delete {self._lock_file}"
                )
            raise
        finally:
            # Release lock
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                logger.debug(f"Released lock on {self.state_path}")
            except Exception as e:
                logger.warning(f"Error releasing lock: {e}")
            finally:
                lock_file.close()

    def validate_markdown(self, content: str) -> List[str]:
        """
        Validate STATE.md markdown format.

        Args:
            content: STATE.md file content

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check 1: Must have workflow header
        if not re.search(r'^# Workflow:', content, re.MULTILINE):
            errors.append("Missing '# Workflow:' header")

        # Check 2: Must have status line with Wave X/Y
        if not re.search(r'Wave\s+\d+/\d+', content):
            errors.append("Missing 'Wave X/Y' status line")

        # Check 3: Must have at least one section header
        if not re.search(r'^## ', content, re.MULTILINE):
            errors.append("Missing sections (## Completed, ## In Progress, etc.)")

        # Check 4: Checkboxes must be valid
        invalid_lines = re.findall(r'^- \[[^x~ ]\]', content, re.MULTILINE)
        if invalid_lines:
            errors.append(f"Invalid checkbox format in {len(invalid_lines)} lines")

        # Check 5: Workflow ID should be present
        if not re.search(r'Workflow ID:', content):
            errors.append("Missing Workflow ID")

        # Check 6: Started timestamp should be present
        if not re.search(r'Started:', content):
            errors.append("Missing Started timestamp")

        # Check 7: Updated timestamp should be present
        if not re.search(r'Updated:', content):
            errors.append("Missing Updated timestamp")

        return errors

    def _write_state_atomic(self, workflow_state: WorkflowState) -> None:
        """
        Write state atomically with backup.

        This ensures that even if the write fails, we have a backup:
        1. Create backup of existing file (if it exists)
        2. Write to temp file
        3. Validate new content
        4. Atomic rename

        Args:
            workflow_state: WorkflowState to write
        """
        content = workflow_state.to_markdown()

        # Validate content before writing
        errors = self.validate_markdown(content)
        if errors:
            logger.warning(f"Markdown validation warnings: {errors}")
            # Continue anyway - these are warnings, not hard failures

        # 1. Create backup if file exists
        if self.state_path.exists():
            logger.debug(f"Creating backup: {self._backup_path}")
            shutil.copy2(self.state_path, self._backup_path)

        # 2. Write to temp file
        temp_path = self.state_path.with_suffix('.tmp')
        temp_path.write_text(content, encoding='utf-8')

        # 3. Atomic rename
        temp_path.rename(self.state_path)
        logger.debug(f"Written state to {self.state_path}")

    def parse_state(self, content: str) -> Optional[WorkflowState]:
        """
        Parse STATE.md content and return WorkflowState.

        Args:
            content: STATE.md file content

        Returns:
            WorkflowState if parsing successful, None otherwise
        """
        # Validate markdown before parsing
        errors = self.validate_markdown(content)
        if errors:
            logger.warning(f"STATE.md validation errors: {errors}")
            # Continue parsing - these are warnings, not hard failures

        try:
            lines = content.splitlines()

            # Extract workflow name from first header
            workflow_name = "Unknown"
            workflow_id = "unknown"
            for line in lines:
                if line.startswith("# Workflow:"):
                    workflow_name = line[12:].strip()  # Remove "# Workflow:" prefix (12 chars)
                    break
                elif line.startswith("# "):
                    workflow_name = line[2:].strip()
                    break

            # Extract workflow ID
            for line in lines:
                if "Workflow ID:" in line:
                    match = re.search(r'`([^`]+)`', line)
                    if match:
                        workflow_id = match.group(1)
                        break

            # Extract status line
            current_wave = 0
            total_waves = 0
            for line in lines:
                if "Wave" in line and "/" in line:
                    match = re.search(r'Wave (\d+)/(\d+)', line)
                    if match:
                        current_wave = int(match.group(1))
                        total_waves = int(match.group(2))
                        break

            # Parse tasks
            tasks = {}
            current_section = None
            task_wave = 0  # Renamed to avoid conflict with outer current_wave

            for line in lines:
                # Track sections
                if "## ✅ Completed" in line or "## Completed" in line:
                    current_section = "completed"
                elif "## 🔄 In Progress" in line or "## In Progress" in line:
                    current_section = "in_progress"
                elif "## 📋 Pending" in line or "## Pending" in line:
                    current_section = "pending"
                elif "## ❌ Failed" in line or "## Failed" in line:
                    current_section = "failed"
                elif line.startswith("### Wave "):
                    match = re.search(r'Wave (\d+)', line)
                    if match:
                        task_wave = int(match.group(1))

                # Parse task lines
                elif line.strip().startswith("- [") and "**" in line:
                    task_match = re.search(r'\*\*([^*]+)\*\*:\s*(.+)', line)
                    if task_match:
                        task_id = task_match.group(1).strip()
                        description = task_match.group(2).strip()

                        # Determine status from checkbox
                        if "- [x]" in line:
                            task_status = "completed"
                        elif "- [~]" in line:
                            task_status = "in_progress"
                        else:
                            task_status = current_section or "pending"

                        # Remove "(IN PROGRESS)" suffix if present
                        description = re.sub(r'\s*\(IN PROGRESS\)\s*$', '', description)

                        # Skip if already exists (prefer first occurrence)
                        if task_id not in tasks:
                            tasks[task_id] = TaskState(
                                task_id=task_id,
                                description=description,
                                status=task_status,
                                wave_id=task_wave
                            )

                # Parse commit hash (next line after task)
                elif line.strip().startswith("- Commit:") and tasks:
                    # Find most recently added task
                    last_task_id = list(tasks.keys())[-1]
                    match = re.search(r'`([^`]+)`', line)
                    if match:
                        tasks[last_task_id].commit_hash = match.group(1)

                # Parse files modified
                elif line.strip().startswith("- Files:") and tasks:
                    last_task_id = list(tasks.keys())[-1]
                    files_str = re.sub(r'-\s*Files:\s*', '', line)
                    # Simple parse - could be improved
                    if files_str.strip():
                        tasks[last_task_id].files_modified = [files_str.strip()]

                # Parse error
                elif line.strip().startswith("- Error:") and tasks:
                    last_task_id = list(tasks.keys())[-1]
                    error_str = re.sub(r'-\s*Error:\s*', '', line)
                    tasks[last_task_id].error = error_str.strip()
                    tasks[last_task_id].status = "failed"

            # Parse timestamps
            started_at = datetime.now()
            updated_at = datetime.now()
            for line in lines:
                if "Started:" in line:
                    try:
                        started_at = datetime.strptime(line.split("Started:")[1].strip(), '%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                if "Updated:" in line:
                    try:
                        updated_at = datetime.strptime(line.split("Updated:")[1].strip(), '%Y-%m-%d %H:%M:%S')
                    except:
                        pass

            # Parse notes
            notes = []
            in_notes = False
            for line in lines:
                if line.startswith("## Notes"):
                    in_notes = True
                    continue
                if in_notes:
                    if line.startswith("## "):
                        break
                    if line.strip().startswith("- "):
                        notes.append(line.strip()[2:])

            return WorkflowState(
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                current_wave=current_wave,
                total_waves=total_waves,
                tasks=tasks,
                started_at=started_at,
                updated_at=updated_at,
                notes=notes
            )

        except Exception as e:
            logger.error(f"Failed to parse STATE.md: {e}", exc_info=True)
            return None

    def update(
        self,
        workflow_id: str,
        workflow_name: str,
        wave_id: int,
        total_waves: int,
        completed_tasks: List[Dict[str, Any]],
        current_wave_tasks: List[Dict[str, Any]],
        pending_waves: List[List[Dict[str, Any]]],
        commit_hash: Optional[str] = None,
        notes: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update STATE.md with current workflow status.

        This method uses file locking and retry logic to handle concurrent access safely.

        Args:
            workflow_id: Workflow identifier
            workflow_name: Human-readable workflow name
            wave_id: Current wave number
            total_waves: Total number of waves
            completed_tasks: Tasks from completed waves
            current_wave_tasks: Tasks in current wave
            pending_waves: Tasks in pending waves
            commit_hash: Optional git commit hash for current wave
            notes: Optional notes to add
            metadata: Optional metadata to include

        Raises:
            RuntimeError: If lock cannot be acquired after max_retries
        """
        # Retry logic with exponential backoff
        for attempt in range(self._max_retries):
            try:
                with self._lock_state():
                    # Load existing state to preserve started_at and notes
                    existing_state = None
                    if self.state_path.exists():
                        existing_state = self.load_state()

                    # Build WorkflowState
                    tasks = {}

                    # Add completed tasks
                    for task_dict in completed_tasks:
                        task_id = task_dict.get('task_id', task_dict.get('agent_id', 'unknown'))
                        # Extract task description from various fields
                        description = (
                            task_dict.get('description') or
                            task_dict.get('task') or
                            task_dict.get('prompt', 'Unknown')[:100]
                        )

                        # Get result info
                        result = task_dict.get('result', {})
                        files = []
                        if result:
                            files = result.get('files_modified', result.get('files_created', []))

                        tasks[task_id] = TaskState(
                            task_id=task_id,
                            description=description,
                            status='completed',
                            wave_id=task_dict.get('wave_id', 0),
                            commit_hash=task_dict.get('commit_hash'),
                            files_modified=files,
                            error=task_dict.get('error')
                        )

                    # Add current wave tasks
                    for task_dict in current_wave_tasks:
                        task_id = task_dict.get('task_id', task_dict.get('agent_id', 'unknown'))
                        description = (
                            task_dict.get('description') or
                            task_dict.get('task') or
                            task_dict.get('prompt', 'Unknown')[:100]
                        )

                        # Determine if in progress or pending
                        result = task_dict.get('result')
                        status = 'completed'
                        if result:
                            if result.get('success'):
                                status = 'completed'
                            elif result.get('error'):
                                status = 'failed'
                            else:
                                status = 'in_progress'
                        else:
                            status = 'in_progress'

                        # Get result info
                        files = []
                        if result:
                            files = result.get('files_modified', result.get('files_created', []))

                        # Use current wave commit hash if task doesn't have one
                        task_commit = task_dict.get('commit_hash')
                        if status == 'completed' and not task_commit and commit_hash:
                            task_commit = commit_hash

                        tasks[task_id] = TaskState(
                            task_id=task_id,
                            description=description,
                            status=status,
                            wave_id=wave_id,
                            commit_hash=task_commit,
                            files_modified=files,
                            error=task_dict.get('error') or (result.get('error') if result else None)
                        )

                    # Add pending tasks
                    for wave_num, wave_tasks in enumerate(pending_waves, start=wave_id + 1):
                        for task_dict in wave_tasks:
                            task_id = task_dict.get('task_id', task_dict.get('agent_id', f'wave{wave_num}_task{len(tasks)+1}'))
                            description = (
                                task_dict.get('description') or
                                task_dict.get('task') or
                                task_dict.get('prompt', 'Unknown')[:100]
                            )

                            tasks[task_id] = TaskState(
                                task_id=task_id,
                                description=description,
                                status='pending',
                                wave_id=wave_num
                            )

                    # Preserve or create timestamps
                    started_at = existing_state.started_at if existing_state else datetime.now()
                    updated_at = datetime.now()

                    # Merge notes
                    merged_notes = []
                    if existing_state:
                        merged_notes.extend(existing_state.notes)
                    if notes:
                        merged_notes.extend(notes)

                    # Create WorkflowState
                    workflow_state = WorkflowState(
                        workflow_id=workflow_id,
                        workflow_name=workflow_name,
                        current_wave=wave_id,
                        total_waves=total_waves,
                        tasks=tasks,
                        started_at=started_at,
                        updated_at=updated_at,
                        notes=merged_notes,
                        metadata=metadata or {}
                    )

                    # Write atomically with backup
                    self._write_state_atomic(workflow_state)

                    logger.info(f"Updated STATE.md: Wave {wave_id}/{total_waves}, {len(tasks)} tasks total")
                    return  # Success, exit retry loop

            except RuntimeError as e:
                if "locked by another process" in str(e):
                    if attempt < self._max_retries - 1:
                        # Exponential backoff: 0.5s, 1s, 2s, etc.
                        delay = self._retry_delay * (2 ** attempt)
                        logger.warning(
                            f"STATE.md locked, retrying in {delay}s (attempt {attempt + 1}/{self._max_retries})"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Could not acquire lock after {self._max_retries} attempts")
                        raise
                else:
                    raise

    def load_state(self) -> Optional[WorkflowState]:
        """
        Load workflow state from STATE.md.

        Returns:
            WorkflowState if file exists, None otherwise
        """
        if not self.state_path.exists():
            return None

        content = self.state_path.read_text(encoding='utf-8')
        return self.parse_state(content)

    def get_resume_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information needed to resume a workflow.

        Returns:
            Dictionary with resume info or None if no state exists
        """
        state = self.load_state()
        if not state:
            return None

        # Calculate which wave to resume from
        # Resume from next wave after current
        resume_wave = state.current_wave + 1

        # Check if there are failed tasks in current wave
        failed_tasks = [t for t in state.tasks.values() if t.status == 'failed']
        if failed_tasks:
            # Resume from current wave if there are failures
            resume_wave = state.current_wave

        return {
            'workflow_id': state.workflow_id,
            'workflow_name': state.workflow_name,
            'current_wave': state.current_wave,
            'resume_wave': resume_wave,
            'total_waves': state.total_waves,
            'completed_tasks': [t.task_id for t in state.tasks.values() if t.status == 'completed'],
            'failed_tasks': [t.task_id for t in state.tasks.values() if t.status == 'failed'],
            'pending_tasks': [t.task_id for t in state.tasks.values() if t.status == 'pending'],
            'started_at': state.started_at.isoformat(),
            'updated_at': state.updated_at.isoformat()
        }

    def add_note(self, note: str) -> None:
        """
        Add a note to the current state.

        Args:
            note: Note text to add
        """
        # Retry logic with exponential backoff
        for attempt in range(self._max_retries):
            try:
                with self._lock_state():
                    state = self.load_state()
                    if state:
                        state.notes.append(note)
                        state.updated_at = datetime.now()
                        self._write_state_atomic(state)
                    else:
                        logger.warning("No existing state to add note to")
                    return  # Success, exit retry loop

            except RuntimeError as e:
                if "locked by another process" in str(e):
                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (2 ** attempt)
                        logger.warning(
                            f"STATE.md locked (add_note), retrying in {delay}s "
                            f"(attempt {attempt + 1}/{self._max_retries})"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Could not acquire lock after {self._max_retries} attempts")
                        raise
                else:
                    raise

    def clear(self) -> None:
        """Clear the STATE.md file"""
        if self.state_path.exists():
            self.state_path.unlink()
            logger.info("Cleared STATE.md")

    def initialize(
        self,
        workflow_id: str,
        workflow_name: str,
        total_waves: int,
        all_waves: List[List[Dict[str, Any]]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize a new STATE.md file for a workflow.

        Args:
            workflow_id: Workflow identifier
            workflow_name: Human-readable workflow name
            total_waves: Total number of waves
            all_waves: All waves with their tasks
            metadata: Optional metadata
        """
        # Retry logic with exponential backoff
        for attempt in range(self._max_retries):
            try:
                with self._lock_state():
                    # Build all tasks as pending
                    tasks = {}
                    for wave_num, wave_tasks in enumerate(all_waves, start=1):
                        for task_dict in wave_tasks:
                            task_id = task_dict.get('task_id', task_dict.get('agent_id', f'wave{wave_num}_task{len(tasks)+1}'))
                            description = (
                                task_dict.get('description') or
                                task_dict.get('task') or
                                task_dict.get('prompt', 'Unknown')[:100]
                            )

                            tasks[task_id] = TaskState(
                                task_id=task_id,
                                description=description,
                                status='pending',
                                wave_id=wave_num
                            )

                    # Create initial state
                    workflow_state = WorkflowState(
                        workflow_id=workflow_id,
                        workflow_name=workflow_name,
                        current_wave=0,
                        total_waves=total_waves,
                        tasks=tasks,
                        started_at=datetime.now(),
                        updated_at=datetime.now(),
                        metadata=metadata or {}
                    )

                    # Write atomically with backup
                    self._write_state_atomic(workflow_state)

                    logger.info(f"Initialized STATE.md for workflow '{workflow_name}' with {len(tasks)} tasks across {total_waves} waves")
                    return  # Success, exit retry loop

            except RuntimeError as e:
                if "locked by another process" in str(e):
                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (2 ** attempt)
                        logger.warning(
                            f"STATE.md locked (initialize), retrying in {delay}s "
                            f"(attempt {attempt + 1}/{self._max_retries})"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Could not acquire lock after {self._max_retries} attempts")
                        raise
                else:
                    raise
