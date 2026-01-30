import argparse
import time
from typing import Optional
from ..data.storage import TaskStorage, FractalTask
from ..logic.decomposition import Decomposer
from ..integration.atomic_timeline import AtomicTimeline

class FractalGenesisManager:
    def __init__(self):
        self.storage = TaskStorage()
        self.decomposer = Decomposer()
        self.timeline = AtomicTimeline()

    def start_new_task(self, objective: str) -> FractalTask:
        """
        Starts a new Fractal Genesis task.
        1. Creates task record.
        2. Decomposes into 10 initial principles.
        3. Commits the initialization.
        """
        # 1. Create Task
        task_id = f"FG-{int(time.time())}"
        task = self.storage.create_task(task_id, objective)
        print(f"Created Task: {task.id}")
        
        # 2. Decompose (Level 1)
        print("Decomposing into 10 First Principles...")
        subtasks = self.decomposer.decompose(objective)
        task.subtasks = subtasks
        self.storage.save_task(task)
        
        # 3. Atomic Commit
        self.timeline.commit_step(task.id, "Initialized task and Level 1 decomposition", {"depth": 0})
        
        return task

    def process_task(self, task_id: str):
        """
        Main recursive loop would go here.
        For now, this just prints the status.
        """
        task = self.storage.load_task(task_id)
        if not task:
            print(f"Task {task_id} not found.")
            return

        print(f"Processing Task: {task.objective}")
        for st in task.subtasks:
            print(f" - [ ] {st.title}")

def main():
    parser = argparse.ArgumentParser(description="Fractal Genesis CLI")
    parser.add_argument("action", choices=["new", "resume", "status"], help="Action to perform")
    parser.add_argument("--objective", "-o", help="Objective for new task")
    parser.add_argument("--id", "-i", help="Task ID for resume/status")
    
    args = parser.parse_args()
    manager = FractalGenesisManager()

    if args.action == "new":
        if not args.objective:
            print("Error: --objective is required for 'new' action")
            return
        manager.start_new_task(args.objective)
        
    elif args.action == "status":
        if not args.id:
            print("Error: --id is required for 'status' action")
            return
        manager.process_task(args.id)

if __name__ == "__main__":
    main()
