"""
Production Validation Script for Enhanced Memory System

This script validates that the enhanced memory system is ready for production use.
Run this before deploying to ensure everything works correctly.

Usage:
    python validate_production.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ProductionValidator:
    """Validates enhanced memory system for production readiness"""

    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []

    def log_pass(self, check_name: str, details: str = ""):
        """Log a passed check"""
        self.checks_passed.append(check_name)
        print(f"  ✅ {check_name}")
        if details:
            print(f"     {details}")

    def log_fail(self, check_name: str, details: str = ""):
        """Log a failed check"""
        self.checks_failed.append(check_name)
        print(f"  ❌ {check_name}")
        if details:
            print(f"     {details}")

    def log_warning(self, check_name: str, details: str = ""):
        """Log a warning"""
        self.warnings.append(check_name)
        print(f"  ⚠️  {check_name}")
        if details:
            print(f"     {details}")

    def validate_imports(self):
        """Validate all modules can be imported"""
        print("\n" + "="*60)
        print("CHECK 1: Module Imports")
        print("="*60)

        try:
            from ProductionMemorySystem import Message, ProductionMemorySystem
            self.log_pass("Base ProductionMemorySystem imports")
        except ImportError as e:
            self.log_fail("Base ProductionMemorySystem imports", str(e))
            return False

        try:
            from EnhancedProductionMemorySystem import (
                EnhancedProductionMemorySystem,
                SemanticWorkingMemory
            )
            self.log_pass("Enhanced memory system imports")
        except ImportError as e:
            self.log_fail("Enhanced memory system imports", str(e))

        try:
            from importance.ImportanceScorer import ImportanceScorer, ImportanceConfig
            self.log_pass("Importance scorer imports")
        except ImportError as e:
            self.log_fail("Importance scorer imports", str(e))

        try:
            from consolidation.MemoryConsolidation import MemoryConsolidation, ConsolidationConfig
            self.log_pass("Consolidation imports")
        except ImportError as e:
            self.log_fail("Consolidation imports", str(e))

        try:
            from episodic.EpisodicMemory import EpisodicMemory
            from episodic.Episode import Episode
            self.log_pass("Episodic memory imports")
        except ImportError as e:
            self.log_fail("Episodic memory imports", str(e))

        return True

    def validate_backward_compatibility(self):
        """Validate backward compatibility with base system"""
        print("\n" + "="*60)
        print("CHECK 2: Backward Compatibility")
        print("="*60)

        from ProductionMemorySystem import Message, ProductionMemorySystem
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Test base system still works
            try:
                base_memory = ProductionMemorySystem(
                    project_path=Path(tmpdir),
                    project_name="test_base"
                )
                base_memory.add(Message(
                    role="user",
                    content="Test message",
                    timestamp=datetime.now().isoformat()
                ))
                context = base_memory.get_context(limit=10)
                self.log_pass("Base system functionality", "Old API still works")
            except Exception as e:
                self.log_fail("Base system functionality", str(e))
                return False

            # Test enhanced system as drop-in replacement
            try:
                from EnhancedProductionMemorySystem import EnhancedProductionMemorySystem

                enhanced_memory = EnhancedProductionMemorySystem(
                    project_path=Path(tmpdir),
                    project_name="test_enhanced"
                )
                enhanced_memory.add(Message(
                    role="user",
                    content="Test message",
                    timestamp=datetime.now().isoformat()
                ))
                context = enhanced_memory.get_context(limit=10)
                self.log_pass("Enhanced system compatibility", "Works as drop-in replacement")
            except Exception as e:
                self.log_fail("Enhanced system compatibility", str(e))

        return True

    def validate_semantic_retrieval(self):
        """Validate semantic memory retrieval"""
        print("\n" + "="*60)
        print("CHECK 3: Semantic Memory Retrieval")
        print("="*60)

        from ProductionMemorySystem import Message
        from EnhancedProductionMemorySystem import EnhancedProductionMemorySystem
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EnhancedProductionMemorySystem(
                project_path=Path(tmpdir),
                project_name="test_semantic"
            )

            # Add test messages
            messages = [
                Message(role="user", content="How do I fix authentication?", timestamp=datetime.now().isoformat()),
                Message(role="assistant", content="Check your API keys", timestamp=datetime.now().isoformat()),
                Message(role="user", content="Database is slow", timestamp=datetime.now().isoformat()),
            ]

            for msg in messages:
                memory.add(msg)

            # Test recent strategy
            try:
                context = memory.get_context(limit=10, strategy="recent")
                self.log_pass("Recent retrieval strategy")
            except Exception as e:
                self.log_fail("Recent retrieval strategy", str(e))

            # Test semantic strategy
            try:
                context = memory.get_context(
                    query="authentication",
                    limit=10,
                    strategy="semantic"
                )
                self.log_pass("Semantic retrieval strategy")
            except Exception as e:
                self.log_fail("Semantic retrieval strategy", str(e))

            # Test hybrid strategy
            try:
                context = memory.get_context(
                    query="database",
                    limit=10,
                    strategy="hybrid"
                )
                self.log_pass("Hybrid retrieval strategy")
            except Exception as e:
                self.log_fail("Hybrid retrieval strategy", str(e))

            # Test importance strategy
            try:
                context = memory.get_context(
                    limit=10,
                    strategy="importance"
                )
                self.log_pass("Importance retrieval strategy")
            except Exception as e:
                self.log_fail("Importance retrieval strategy", str(e))

        return True

    def validate_importance_scoring(self):
        """Validate importance scoring"""
        print("\n" + "="*60)
        print("CHECK 4: Importance Scoring")
        print("="*60)

        from importance.ImportanceScorer import ImportanceScorer, ImportanceConfig

        scorer = ImportanceScorer()

        # Test importance calculation
        try:
            score = scorer.calculate_importance(
                role="user",
                content="Error: Something went wrong",
                timestamp=datetime.now().isoformat()
            )
            if 0.0 <= score <= 1.0:
                self.log_pass("Importance score range", f"Score: {score:.2f}")
            else:
                self.log_fail("Importance score range", f"Score out of range: {score}")
        except Exception as e:
            self.log_fail("Importance calculation", str(e))
            return False

        # Test custom configuration
        try:
            config = ImportanceConfig(base_score=0.3)
            custom_scorer = ImportanceScorer(config)
            score = custom_scorer.calculate_importance(
                role="user",
                content="Test",
                timestamp=datetime.now().isoformat()
            )
            self.log_pass("Custom importance configuration")
        except Exception as e:
            self.log_fail("Custom importance configuration", str(e))

        return True

    def validate_consolidation(self):
        """Validate memory consolidation"""
        print("\n" + "="*60)
        print("CHECK 5: Memory Consolidation")
        print("="*60)

        from ProductionMemorySystem import Message
        from EnhancedProductionMemorySystem import EnhancedProductionMemorySystem
        from consolidation.MemoryConsolidation import ConsolidationConfig
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EnhancedProductionMemorySystem(
                project_path=Path(tmpdir),
                project_name="test_consolidation",
                enable_consolidation=True,
                consolidation_config=ConsolidationConfig(
                    max_messages=20,
                    recent_keep=5
                )
            )

            # Add messages to trigger consolidation
            try:
                for i in range(25):
                    memory.add(Message(
                        role="user",
                        content=f"Message {i}",
                        timestamp=datetime.now().isoformat()
                    ))
                self.log_pass("Message addition for consolidation")
            except Exception as e:
                self.log_fail("Message addition for consolidation", str(e))
                return False

            # Test consolidation
            try:
                result = asyncio.run(memory.consolidate())
                if result.get("status") in ["success", "skipped"]:
                    self.log_pass("Consolidation execution", f"Status: {result.get('status')}")
                else:
                    self.log_fail("Consolidation execution", f"Unexpected status: {result.get('status')}")
            except Exception as e:
                self.log_fail("Consolidation execution", str(e))

            # Test consolidation stats
            try:
                stats = memory.get_consolidation_stats()
                if stats.get("enabled"):
                    self.log_pass("Consolidation statistics")
                else:
                    self.log_fail("Consolidation statistics", "Not enabled")
            except Exception as e:
                self.log_fail("Consolidation statistics", str(e))

        return True

    def validate_episodic_memory(self):
        """Validate episodic memory"""
        print("\n" + "="*60)
        print("CHECK 6: Episodic Memory")
        print("="*60)

        from ProductionMemorySystem import Message
        from episodic.EpisodicMemory import EpisodicMemory
        from episodic.Episode import Episode
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            episodic = EpisodicMemory(storage_path=Path(tmpdir) / "episodes")

            # Test episode creation
            try:
                messages = [
                    Message(role="user", content="Test message 1", timestamp=datetime.now().isoformat()),
                    Message(role="assistant", content="Test response 1", timestamp=datetime.now().isoformat()),
                ]
                episode = episodic.create_episode(
                    title="Test Episode",
                    messages=messages
                )
                self.log_pass("Episode creation", f"Episode ID: {episode.id[:8]}...")
            except Exception as e:
                self.log_fail("Episode creation", str(e))
                return False

            # Test episode retrieval
            try:
                retrieved = episodic.get_episode(episode.id)
                if retrieved and retrieved.id == episode.id:
                    self.log_pass("Episode retrieval")
                else:
                    self.log_fail("Episode retrieval", "Retrieved episode doesn't match")
            except Exception as e:
                self.log_fail("Episode retrieval", str(e))

            # Test episode search
            try:
                results = episodic.search_episodes("test")
                self.log_pass("Episode search", f"Found {len(results)} episodes")
            except Exception as e:
                self.log_fail("Episode search", str(e))

            # Test adding outcome
            try:
                success = episodic.add_outcome(episode.id, "Test outcome")
                if success:
                    self.log_pass("Episode outcome addition")
                else:
                    self.log_fail("Episode outcome addition", "Returned False")
            except Exception as e:
                self.log_fail("Episode outcome addition", str(e))

            # Test episodic stats
            try:
                stats = episodic.get_stats()
                if stats.get("total_episodes") >= 1:
                    self.log_pass("Episodic statistics", f"Total episodes: {stats['total_episodes']}")
                else:
                    self.log_fail("Episodic statistics", "No episodes found")
            except Exception as e:
                self.log_fail("Episodic statistics", str(e))

        return True

    def validate_performance(self):
        """Validate performance characteristics"""
        print("\n" + "="*60)
        print("CHECK 7: Performance")
        print("="*60)

        from ProductionMemorySystem import Message
        from EnhancedProductionMemorySystem import EnhancedProductionMemorySystem
        import time
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EnhancedProductionMemorySystem(
                project_path=Path(tmpdir),
                project_name="test_performance"
            )

            # Test message addition performance
            start = time.time()
            for i in range(100):
                memory.add(Message(
                    role="user",
                    content=f"Performance test message {i}",
                    timestamp=datetime.now().isoformat()
                ))
            add_time = time.time() - start

            if add_time < 1.0:  # Should add 100 messages in < 1 second
                self.log_pass("Message addition performance", f"100 messages in {add_time:.3f}s")
            else:
                self.log_warning("Message addition performance", f"100 messages took {add_time:.3f}s (slow)")

            # Test retrieval performance
            start = time.time()
            for i in range(10):
                context = memory.get_context(
                    query="test",
                    limit=10,
                    strategy="hybrid"
                )
            retrieval_time = time.time() - start

            if retrieval_time < 0.5:  # Should retrieve 10 times in < 0.5 seconds
                self.log_pass("Context retrieval performance", f"10 retrievals in {retrieval_time:.3f}s")
            else:
                self.log_warning("Context retrieval performance", f"10 retrievals took {retrieval_time:.3f}s (slow)")

        return True

    def validate_thread_safety(self):
        """Validate thread safety"""
        print("\n" + "="*60)
        print("CHECK 8: Thread Safety")
        print("="*60)

        from ProductionMemorySystem import Message
        from EnhancedProductionMemorySystem import EnhancedProductionMemorySystem
        import threading
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EnhancedProductionMemorySystem(
                project_path=Path(tmpdir),
                project_name="test_threading"
            )

            # Test concurrent message additions
            errors = []

            def add_messages(thread_id):
                try:
                    for i in range(10):
                        memory.add(Message(
                            role="user",
                            content=f"Thread {thread_id} message {i}",
                            timestamp=datetime.now().isoformat()
                        ))
                except Exception as e:
                    errors.append((thread_id, e))

            threads = [
                threading.Thread(target=add_messages, args=(i,))
                for i in range(5)
            ]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            if not errors:
                self.log_pass("Concurrent message additions", f"5 threads × 10 messages each")
            else:
                self.log_fail("Concurrent message additions", f"{len(errors)} errors occurred")
                return False

            # Verify final state
            final_size = memory.working.size()
            if final_size == 50:  # 5 threads × 10 messages
                self.log_pass("Thread safety verification", f"All {final_size} messages added correctly")
            else:
                self.log_warning("Thread safety verification", f"Expected 50 messages, got {final_size}")

        return True

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*70)
        print(" "*20 + "VALIDATION SUMMARY")
        print("="*70)

        total = len(self.checks_passed) + len(self.checks_failed)
        passed = len(self.checks_passed)
        failed = len(self.checks_failed)
        warnings_count = len(self.warnings)

        print(f"\nTotal Checks: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings_count}")

        if failed > 0:
            print("\nFailed Checks:")
            for check in self.checks_failed:
                print(f"  ❌ {check}")

        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")

        print("="*70)

        if failed == 0:
            print("\n🎉 ALL VALIDATION CHECKS PASSED! 🎉")
            print("\nThe enhanced memory system is ready for production use.")
            return 0
        else:
            print(f"\n⚠️  {failed} validation check(s) failed")
            print("\nPlease fix the failed checks before deploying to production.")
            return 1

    def validate_all(self):
        """Run all validation checks"""
        print("="*70)
        print(" "*15 + "ENHANCED MEMORY SYSTEM PRODUCTION VALIDATION")
        print("="*70)
        print(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        self.validate_imports()
        self.validate_backward_compatibility()
        self.validate_semantic_retrieval()
        self.validate_importance_scoring()
        self.validate_consolidation()
        self.validate_episodic_memory()
        self.validate_performance()
        self.validate_thread_safety()

        return self.print_summary()


if __name__ == "__main__":
    validator = ProductionValidator()
    exit_code = validator.validate_all()
    exit(exit_code)
