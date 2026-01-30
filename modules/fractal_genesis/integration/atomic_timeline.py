import subprocess
from typing import Optional

class AtomicTimeline:
    """
    Manages the Atomic Commit timeline for tasks.
    Every major step in the Fractal Genesis process is committed to git.
    """
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, args: list) -> bool:
        try:
            subprocess.run(["git"] + args, cwd=self.repo_path, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def commit_step(self, task_id: str, step_description: str, metadata: Optional[dict] = None) -> bool:
        """
        Creates an atomic commit for a specific task step.
        """
        # 1. Stage all changes (in a real agent loop, we might be more selective)
        self._run_git(["add", "."])
        
        # 2. Construct commit message
        message = f"[Fractal Genesis] {task_id}: {step_description}"
        if metadata:
            message += f"\n\nActive Depth: {metadata.get('depth', 0)}"
            
        # 3. Commit
        return self._run_git(["commit", "-m", message])

    def rollback(self, steps: int = 1):
        """
        Reverts the last N atomic commits.
        """
        # This is dangerous, so we might just reset --soft to keep changes staged
        self._run_git(["reset", "--soft", f"HEAD~{steps}"])
