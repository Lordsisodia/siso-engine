#!/usr/bin/env python3
"""
Blackbox4 Semantic Search with True Embeddings
Upgraded with GLM API and local model support
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re

# Import hybrid embedder
from hybrid_embedder import HybridEmbedder


class SemanticContextSearch:
    """Semantic search across all Blackbox4 work using true embeddings"""

    def __init__(self, blackbox_root: str = None, use_embeddings: bool = True):
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
        self.vector_index_file = self.blackbox_root / ".memory/extended/vector-index.json"

        # Initialize embedder
        self.use_embeddings = use_embeddings
        if use_embeddings:
            try:
                self.embedder = HybridEmbedder()
                self.embedding_dim = self.embedder.get_embedding_dim()
                print(f"✓ Hybrid embedder initialized (dim: {self.embedding_dim})")
            except Exception as e:
                print(f"Warning: Embedder initialization failed: {e}")
                print("Falling back to keyword-based search")
                self.embedder = None
                self.use_embeddings = False
        else:
            self.embedder = None

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
                except:
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
                    "description": task.get("description", ""),
                    "priority": task.get("priority"),
                    "status": task.get("status"),
                    "keywords": self._extract_keywords(f"{task['title']} {task.get('description', '')}")
                })

        # Index Ralph work sessions
        if self.ralph_work_dir.exists():
            for session_dir in self.ralph_work_dir.glob("session-*"):
                index["artifacts"].append({
                    "type": "ralph-session",
                    "path": str(session_dir),
                    "keywords": self._extract_keywords_from_session(session_dir)
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
        """Extract keywords from text (fallback method)"""
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

    def search(self, query: str, max_results: int = 10, use_embeddings: Optional[bool] = None) -> Dict:
        """
        Search for past work by meaning

        Args:
            query: Natural language query
            max_results: Maximum results to return
            use_embeddings: Force embedding usage (True/False/None for auto)

        Returns:
            Search results with relevant tasks, contexts, artifacts, and expert agents
        """
        # Determine if we should use embeddings
        if use_embeddings is None:
            use_embeddings = self.use_embeddings and self.embedder is not None

        if use_embeddings and self.embedder:
            return self._embedding_search(query, max_results)
        else:
            return self._keyword_search(query, max_results)

    def _embedding_search(self, query: str, max_results: int) -> Dict:
        """Search using true semantic embeddings"""
        # Generate query embedding
        query_embedding = self.embedder.embed(query)

        results = {
            "query": query,
            "method": "semantic_embedding",
            "relevant_tasks": [],
            "similar_contexts": [],
            "related_artifacts": [],
            "expert_agents": [],
            "total_matches": 0
        }

        # Calculate similarities for all items
        all_items = []

        # Add tasks with their text content
        for task in self.semantic_index.get("tasks", []):
            task_text = f"{task['title']} {task.get('description', '')}"
            all_items.append({
                "type": "task",
                "data": task,
                "text": task_text
            })

        # Add artifacts
        for artifact in self.semantic_index.get("artifacts", []):
            all_items.append({
                "type": "artifact",
                "data": artifact,
                "text": " ".join(artifact.get("keywords", []))
            })

        # Calculate embeddings and similarities for all items
        for item in all_items:
            try:
                item_embedding = self.embedder.embed(item["text"])
                similarity = self._cosine_similarity(query_embedding, item_embedding)

                if similarity > 0.3:  # Threshold for relevance
                    if item["type"] == "task":
                        results["relevant_tasks"].append({
                            **item["data"],
                            "relevance_score": similarity
                        })
                    elif item["type"] == "artifact":
                        results["related_artifacts"].append({
                            **item["data"],
                            "relevance_score": similarity
                        })
            except Exception as e:
                # Fallback to keyword matching for this item
                pass

        # Sort by relevance
        results["relevant_tasks"].sort(key=lambda x: x["relevance_score"], reverse=True)
        results["related_artifacts"].sort(key=lambda x: x["relevance_score"], reverse=True)

        # Keep top results
        results["relevant_tasks"] = results["relevant_tasks"][:max_results]
        results["related_artifacts"] = results["related_artifacts"][:max_results]

        # Find expert agents (keyword-based for now)
        query_keywords = self._extract_keywords(query)
        agent_expertise = self.semantic_index.get("agents", {})
        agent_scores = []

        for agent, expertise in agent_expertise.items():
            score = sum(
                expertise.get("keywords", {}).get(keyword, 0)
                for keyword in query_keywords
            )

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

    def _keyword_search(self, query: str, max_results: int) -> Dict:
        """Search using keyword matching (fallback)"""
        # Extract query keywords
        query_keywords = self._extract_keywords(query)

        results = {
            "query": query,
            "method": "keyword_matching",
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
            score = sum(
                expertise.get("keywords", {}).get(keyword, 0)
                for keyword in query_keywords
            )

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

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np

        a = np.array(vec1)
        b = np.array(vec2)

        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def _calculate_relevance(self, query_keywords: List[str], document_keywords: List[str]) -> float:
        """Calculate relevance score between query and document (keyword-based)"""
        if not query_keywords or not document_keywords:
            return 0.0

        # Count matching keywords
        matches = sum(1 for kw in query_keywords if kw in document_keywords)

        # Calculate score based on matches
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

    def get_status(self) -> Dict:
        """Get system status"""
        status = {
            "index_loaded": True,
            "use_embeddings": self.use_embeddings,
            "embedder_available": self.embedder is not None
        }

        if self.embedder:
            status["embedder_status"] = self.embedder.get_backend_status()

        return status


def main():
    """CLI interface for semantic search"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: semantic-search-upgraded.py [command]")
        print("Commands:")
        print("  search <query>              - Search for past work")
        print("  similar <task_id>           - Find tasks similar to given task")
        print("  context <task_id>           - Get all context for a task")
        print("  rebuild                    - Rebuild semantic index")
        print("  status                     - Show system status")
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

    elif sys.argv[1] == "status":
        status = searcher.get_status()
        print(json.dumps(status, indent=2))

    else:
        print(f"Error: Unknown command {sys.argv[1]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
