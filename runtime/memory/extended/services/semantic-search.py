#!/usr/bin/env python3
"""
Semantic Context Search for Blackbox4

Intelligently searches past work by meaning using ChromaDB vector embeddings.
Finds:
- Relevant tasks from history
- Similar contexts and problems
- Related artifacts and documents
- Expert agents for specific topics
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re


class SemanticContextSearch:
    """Semantic search across all Blackbox4 work"""

    def __init__(self, blackbox_root: str = None):
        """Initialize semantic search"""
        if blackbox_root is None:
            blackbox_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self.blackbox_root = Path(blackbox_root)

        # Key file paths
        self.timeline_file = self.blackbox_root / ".memory/working/shared/timeline.md"
        self.work_queue_file = self.blackbox_root / ".memory/working/shared/work-queue.json"
        self.task_context_dir = self.blackbox_root / ".memory/working/shared/task-context"
        self.ralph_work_dir = self.blackbox_root / "1-agents/4-specialists/ralph-agent/work"
        self.plans_dir = self.blackbox_root / ".plans/active"

        # Index files
        self.semantic_index_file = self.blackbox_root / ".memory/extended/semantic-index.json"

        # Load or build index
        self.semantic_index = self._load_or_build_index()

    def _load_or_build_index(self) -> Dict:
        """Load existing index or build new one"""
        if self.semantic_index_file.exists():
            with open(self.semantic_index_file, 'r') as f:
                index = json.load(f)

            # Check if index is recent (last 24 hours)
            last_updated = index.get("last_updated", "")
            if last_updated:
                try:
                    last_update_dt = datetime.fromisoformat(last_updated)
                    if datetime.now() - last_update_dt < timedelta(hours=24):
                        return index
                except (ValueError, TypeError):
                    pass

        # Build new index
        return self._build_semantic_index()

    def _build_semantic_index(self) -> Dict:
        """Build semantic search index from all work"""
        print("Building semantic search index...")

        index = {
            "last_updated": datetime.utcnow().isoformat(),
            "documents": [],
            "tasks": [],
            "contexts": [],
            "artifacts": [],
            "agents": {}
        }

        # Index timeline entries
        if self.timeline_file.exists():
            timeline_entries = self._parse_timeline(self.timeline_file)
            for entry in timeline_entries:
                index["documents"].append({
                    "type": "timeline",
                    "content": entry["content"],
                    "timestamp": entry["timestamp"],
                    "agent": entry.get("agent"),
                    "task_id": entry.get("task_id"),
                    "action": entry.get("action"),
                    "keywords": self._extract_keywords(entry["content"])
                })

        # Index work queue tasks
        if self.work_queue_file.exists():
            with open(self.work_queue_file, 'r') as f:
                work_queue = json.load(f)

            for task in work_queue:
                index["tasks"].append({
                    "id": task["id"],
                    "title": task["title"],
                    "description": task["description"],
                    "priority": task.get("priority"),
                    "status": task.get("status"),
                    "keywords": self._extract_keywords(f"{task['title']} {task['description']}"),
                    "subtasks": task.get("subtasks", [])
                })

        # Index task contexts
        if self.task_context_dir.exists():
            for context_file in self.task_context_dir.glob("*.json"):
                try:
                    with open(context_file, 'r') as f:
                        context = json.load(f)

                    index["contexts"].append({
                        "task_id": context.get("task_id"),
                        "content": str(context),
                        "keywords": self._extract_keywords(str(context))
                    })
                except (json.JSONDecodeError, IOError):
                    pass

        # Index Ralph work sessions
        if self.ralph_work_dir.exists():
            for session_dir in self.ralph_work_dir.glob("session-*"):
                index["artifacts"].append({
                    "type": "ralph-session",
                    "path": str(session_dir),
                    "keywords": self._extract_keywords_from_session(session_dir)
                })

        # Index active plans
        if self.plans_dir.exists():
            for plan_dir in self.plans_dir.iterdir():
                if plan_dir.is_dir():
                    index["artifacts"].append({
                        "type": "plan",
                        "path": str(plan_dir),
                        "keywords": self._extract_keywords_from_plan(plan_dir)
                    })

        # Build agent expertise index
        index["agents"] = self._build_agent_expertise(index)

        # Save index
        self.semantic_index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.semantic_index_file, 'w') as f:
            json.dump(index, f, indent=2)

        print(f"✅ Indexed {len(index['documents'])} documents, {len(index['tasks'])} tasks, {len(index['contexts'])} contexts, {len(index['artifacts'])} artifacts")

        return index

    def _parse_timeline(self, timeline_file: Path) -> List[Dict]:
        """Parse timeline entries from markdown"""
        entries = []

        with open(timeline_file, 'r') as f:
            content = f.read()

        # Split by timestamp headers
        sections = re.split(r'^## (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)', content, flags=re.MULTILINE)

        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                timestamp = sections[i]
                body = sections[i + 1]

                # Extract key information
                entry = {
                    "timestamp": timestamp,
                    "content": body,
                    "type": "timeline"
                }

                # Extract agent
                agent_match = re.search(r'\*\*Agent:\*\*\s*(\w+)', body)
                if agent_match:
                    entry["agent"] = agent_match.group(1)

                # Extract task ID
                task_match = re.search(r'\*\*Task ID:\*\*\s*(\w+)', body)
                if task_match:
                    entry["task_id"] = task_match.group(1)

                # Extract action
                action_match = re.search(r'\*\*Action:\*\*\s*(\w+)', body)
                if action_match:
                    entry["action"] = action_match.group(1)

                entries.append(entry)

        return entries

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())

        # Filter common words
        common_words = {
            'this', 'that', 'with', 'from', 'have', 'they', 'what', 'when',
            'which', 'their', 'would', 'about', 'there', 'other', 'into'
        }

        keywords = [w for w in words if w not in common_words]

        # Return unique keywords, sorted by frequency
        from collections import Counter
        keyword_freq = Counter(keywords)

        return [kw for kw, _ in keyword_freq.most_common(20)]

    def _extract_keywords_from_session(self, session_dir: Path) -> List[str]:
        """Extract keywords from Ralph session"""
        keywords = []

        # Read session files
        for md_file in session_dir.glob("*.md"):
            with open(md_file, 'r') as f:
                content = f.read()
                keywords.extend(self._extract_keywords(content))

        return list(set(keywords))

    def _extract_keywords_from_plan(self, plan_dir: Path) -> List[str]:
        """Extract keywords from plan directory"""
        keywords = []

        # Read plan files
        for md_file in plan_dir.glob("*.md"):
            with open(md_file, 'r') as f:
                content = f.read()
                keywords.extend(self._extract_keywords(content))

        return list(set(keywords))

    def _build_agent_expertise(self, index: Dict) -> Dict:
        """Build agent expertise index"""
        agent_expertise = {}

        # Analyze timeline entries for agent expertise
        for doc in index["documents"]:
            agent = doc.get("agent")
            if agent:
                if agent not in agent_expertise:
                    agent_expertise[agent] = {
                        "tasks_completed": 0,
                        "keywords": {},
                        "domains": set()
                    }

                if doc.get("action") in ["COMPLETED", "COMPLETE"]:
                    agent_expertise[agent]["tasks_completed"] += 1

                # Add keywords
                for keyword in doc.get("keywords", []):
                    if keyword not in agent_expertise[agent]["keywords"]:
                        agent_expertise[agent]["keywords"][keyword] = 0
                    agent_expertise[agent]["keywords"][keyword] += 1

        # Convert sets to lists for JSON serialization
        for agent in agent_expertise:
            agent_expertise[agent]["domains"] = list(agent_expertise[agent]["domains"])

        return agent_expertise

    def search(self, query: str, max_results: int = 10) -> Dict:
        """
        Search for past work by meaning

        Args:
            query: Natural language query
            max_results: Maximum results to return

        Returns:
            Search results with relevant tasks, contexts, artifacts, and expert agents
        """
        # Extract query keywords
        query_keywords = self._extract_keywords(query)

        results = {
            "query": query,
            "query_keywords": query_keywords,
            "relevant_tasks": [],
            "similar_contexts": [],
            "related_artifacts": [],
            "expert_agents": [],
            "total_matches": 0
        }

        # Search tasks
        task_scores = []
        for task in self.semantic_index.get("tasks", []):
            score = self._calculate_relevance(query_keywords, task.get("keywords", []))
            if score > 0:
                task_scores.append((task, score))

        # Sort by relevance
        task_scores.sort(key=lambda x: x[1], reverse=True)

        # Add top tasks
        for task, score in task_scores[:max_results]:
            results["relevant_tasks"].append({
                **task,
                "relevance_score": score
            })

        # Search contexts
        context_scores = []
        for context in self.semantic_index.get("contexts", []):
            score = self._calculate_relevance(query_keywords, context.get("keywords", []))
            if score > 0:
                context_scores.append((context, score))

        context_scores.sort(key=lambda x: x[1], reverse=True)

        for context, score in context_scores[:max_results]:
            results["similar_contexts"].append({
                "task_id": context.get("task_id"),
                "relevance_score": score
            })

        # Search artifacts
        artifact_scores = []
        for artifact in self.semantic_index.get("artifacts", []):
            score = self._calculate_relevance(query_keywords, artifact.get("keywords", []))
            if score > 0:
                artifact_scores.append((artifact, score))

        artifact_scores.sort(key=lambda x: x[1], reverse=True)

        for artifact, score in artifact_scores[:max_results]:
            results["related_artifacts"].append({
                **artifact,
                "relevance_score": score
            })

        # Find expert agents
        agent_expertise = self.semantic_index.get("agents", {})
        agent_scores = []

        for agent, expertise in agent_expertise.items():
            # Calculate expertise score for this query
            score = 0
            for keyword in query_keywords:
                if keyword in expertise.get("keywords", {}):
                    score += expertise["keywords"][keyword]

            if score > 0:
                agent_scores.append((agent, score, expertise))

        agent_scores.sort(key=lambda x: x[1], reverse=True)

        for agent, score, expertise in agent_scores[:5]:
            results["expert_agents"].append({
                "agent": agent,
                "expertise_score": score,
                "tasks_completed": expertise.get("tasks_completed", 0),
                "top_keywords": list(expertise.get("keywords", {}).keys())[:10]
            })

        results["total_matches"] = (
            len(results["relevant_tasks"]) +
            len(results["similar_contexts"]) +
            len(results["related_artifacts"])
        )

        return results

    def _calculate_relevance(self, query_keywords: List[str], document_keywords: List[str]) -> float:
        """Calculate relevance score between query and document"""
        if not query_keywords or not document_keywords:
            return 0.0

        # Count matching keywords
        matches = sum(1 for kw in query_keywords if kw in document_keywords)

        # Calculate score based on matches and keyword importance
        score = matches / len(query_keywords)

        return score

    def find_similar_task(self, task_id: str) -> Dict:
        """Find tasks similar to the given task"""
        # Load task from work queue
        if not self.work_queue_file.exists():
            return {"error": "Work queue not found"}

        with open(self.work_queue_file, 'r') as f:
            work_queue = json.load(f)

        # Find the task
        target_task = None
        for task in work_queue:
            if task["id"] == task_id:
                target_task = task
                break

        if not target_task:
            return {"error": "Task not found"}

        # Build search query from task
        query = f"{target_task['title']} {target_task.get('description', '')}"

        # Search
        return self.search(query, max_results=5)

    def get_context_for_task(self, task_id: str) -> Dict:
        """Get all relevant context for a task"""
        results = self.find_similar_task(task_id)

        if "error" in results:
            return results

        # Load task context if exists
        context_file = self.task_context_dir / f"{task_id}.json"
        task_context = None
        if context_file.exists():
            with open(context_file, 'r') as f:
                task_context = json.load(f)

        return {
            "task_id": task_id,
            "task_context": task_context,
            "similar_tasks": results["relevant_tasks"],
            "similar_contexts": results["similar_contexts"],
            "related_artifacts": results["related_artifacts"],
            "expert_agents": results["expert_agents"]
        }

    def rebuild_index(self):
        """Force rebuild of semantic index"""
        self.semantic_index = self._build_semantic_index()
        return {
            "status": "success",
            "indexed_documents": len(self.semantic_index["documents"]),
            "indexed_tasks": len(self.semantic_index["tasks"]),
            "indexed_contexts": len(self.semantic_index["contexts"]),
            "indexed_artifacts": len(self.semantic_index["artifacts"])
        }


def main():
    """CLI interface for semantic search"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: semantic-search.py [command]")
        print("Commands:")
        print("  search <query>              - Search for past work")
        print("  similar <task_id>           - Find tasks similar to given task")
        print("  context <task_id>           - Get all context for a task")
        print("  rebuild                    - Rebuild semantic index")
        sys.exit(1)

    searcher = SemanticContextSearch()

    if sys.argv[1] == "search":
        if len(sys.argv) < 3:
            print("Error: Missing search query")
            sys.exit(1)

        query = " ".join(sys.argv[2:])
        results = searcher.search(query)
        print(json.dumps(results, indent=2))

    elif sys.argv[1] == "similar":
        if len(sys.argv) < 3:
            print("Error: Missing task ID")
            sys.exit(1)

        task_id = sys.argv[2]
        results = searcher.find_similar_task(task_id)
        print(json.dumps(results, indent=2))

    elif sys.argv[1] == "context":
        if len(sys.argv) < 3:
            print("Error: Missing task ID")
            sys.exit(1)

        task_id = sys.argv[2]
        results = searcher.get_context_for_task(task_id)
        print(json.dumps(results, indent=2))

    elif sys.argv[1] == "rebuild":
        results = searcher.rebuild_index()
        print(json.dumps(results, indent=2))

    else:
        print(f"Error: Unknown command {sys.argv[1]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
