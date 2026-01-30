#!/usr/bin/env python3
"""
Pipeline Integration Layer for SISO-INTERNAL

Integrates the new Pipeline System with existing SISO-INTERNAL infrastructure:
- EventBus for event publishing
- ProductionMemorySystem for state persistence
- AgentLoader for agent discovery
- SkillManager for skill composition
- TaskRouter for intelligent routing

This ensures the pipeline works seamlessly with the broader system.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

import yaml


class PipelineIntegration:
    """
    Integration layer that connects the Pipeline System with SISO-INTERNAL infrastructure.

    Responsibilities:
    1. Publish pipeline events to EventBus
    2. Persist pipeline state to ProductionMemorySystem
    3. Load agents via AgentLoader
    4. Compose skills via SkillManager
    5. Route tasks intelligently
    """

    def __init__(self, blackbox_root: Path):
        self.blackbox_root = Path(blackbox_root)
        self.engine_dir = self.blackbox_root / "engine"

        # Add to path
        if str(self.engine_dir) not in sys.path:
            sys.path.insert(0, str(self.engine_dir))

        # Integration flags
        self.has_event_bus = False
        self.has_memory_system = False
        self.has_agent_loader = False
        self.has_skill_manager = False

        # Initialize integrations
        self._init_event_bus()
        self._init_memory_system()
        self._init_agent_loader()
        self._init_skill_manager()

    def _init_event_bus(self):
        """Initialize EventBus integration"""
        try:
            from core.event_bus import RedisEventBus, EventBusConfig, EventBusState

            # Try to connect to Redis
            config = EventBusConfig(db=14)  # Use different DB for pipeline
            self.event_bus = RedisEventBus(config)

            try:
                self.event_bus.connect()
                if self.event_bus.state == EventBusState.CONNECTED:
                    self.has_event_bus = True
                    print("✅ Pipeline: Connected to EventBus")
            except Exception as e:
                print(f"⚠️  Pipeline: EventBus unavailable ({e})")
                self.event_bus = None

        except ImportError:
            print("⚠️  Pipeline: EventBus module not found")
            self.event_bus = None

    def _init_memory_system(self):
        """Initialize ProductionMemorySystem integration"""
        try:
            from memory.ProductionMemorySystem import ProductionMemorySystem

            self.memory_system = ProductionMemorySystem(
                project_root=str(self.blackbox_root)
            )
            self.has_memory_system = True
            print("✅ Pipeline: Connected to ProductionMemorySystem")

        except Exception as e:
            print(f"⚠️  Pipeline: Memory system unavailable ({e})")
            self.memory_system = None

    def _init_agent_loader(self):
        """Initialize AgentLoader integration"""
        try:
            from agents.core.AgentLoader import AgentLoader

            self.agent_loader = AgentLoader(
                agents_dir=self.blackbox_root / "engine" / "agents"
            )
            self.has_agent_loader = True
            print("✅ Pipeline: Connected to AgentLoader")

        except Exception as e:
            print(f"⚠️  Pipeline: AgentLoader unavailable ({e})")
            self.agent_loader = None

    def _init_skill_manager(self):
        """Initialize SkillManager integration"""
        try:
            from agents.core.SkillManager import SkillManager

            self.skill_manager = SkillManager(
                skills_dir=self.blackbox_root / "engine" / "agents" / ".skills"
            )
            self.has_skill_manager = True
            print("✅ Pipeline: Connected to SkillManager")

        except Exception as e:
            print(f"⚠️  Pipeline: SkillManager unavailable ({e})")
            self.skill_manager = None

    def publish_pipeline_event(
        self,
        event_type: str,
        pipeline_type: str,
        data: Dict[str, Any]
    ):
        """
        Publish a pipeline event to the EventBus.

        Args:
            event_type: Type of event (feature_proposed, feature_reviewed, etc.)
            pipeline_type: Type of pipeline (feature, testing, unified)
            data: Event data
        """
        if not self.has_event_bus:
            return

        try:
            from core.event_bus import TaskEvent

            event = TaskEvent(
                event_type=f"pipeline.{pipeline_type}.{event_type}",
                data={
                    'timestamp': datetime.utcnow().isoformat(),
                    'pipeline_type': pipeline_type,
                    **data
                }
            )

            self.event_bus.publish(
                topic="pipeline.events",
                event=event
            )

        except Exception as e:
            print(f"⚠️  Failed to publish event: {e}")

    def save_pipeline_state(
        self,
        pipeline_type: str,
        run_id: str,
        state: Dict[str, Any]
    ):
        """
        Save pipeline state to ProductionMemorySystem.

        Args:
            pipeline_type: Type of pipeline (feature, testing, unified)
            run_id: Unique run identifier
            state: State data to persist
        """
        if not self.has_memory_system:
            return

        try:
            # Save to working memory
            self.memory_system.working_memory.save_context(
                session_id=f"pipeline_{pipeline_type}_{run_id}",
                context=state
            )

        except Exception as e:
            print(f"⚠️  Failed to save state: {e}")

    def load_pipeline_state(
        self,
        pipeline_type: str,
        run_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load pipeline state from ProductionMemorySystem.

        Args:
            pipeline_type: Type of pipeline
            run_id: Unique run identifier

        Returns:
            State data if found, None otherwise
        """
        if not self.has_memory_system:
            return None

        try:
            context = self.memory_system.working_memory.load_context(
                session_id=f"pipeline_{pipeline_type}_{run_id}"
            )
            return context

        except Exception as e:
            print(f"⚠️  Failed to load state: {e}")
            return None

    def get_available_agents(self) -> List[str]:
        """
        Get list of available agents from AgentLoader.

        Returns:
            List of agent names
        """
        if not self.has_agent_loader:
            return []

        try:
            agents = self.agent_loader.list_agents()
            return list(agents.keys())

        except Exception as e:
            print(f"⚠️  Failed to load agents: {e}")
            return []

    def get_available_skills(self) -> List[str]:
        """
        Get list of available skills from SkillManager.

        Returns:
            List of skill names
        """
        if not self.has_skill_manager:
            return []

        try:
            skills = self.skill_manager.list_skills()
            return list(skills.keys())

        except Exception as e:
            print(f"⚠️  Failed to load skills: {e}")
            return []

    def get_integration_status(self) -> Dict[str, bool]:
        """
        Get status of all integrations.

        Returns:
            Dictionary with integration status
        """
        return {
            'event_bus': self.has_event_bus,
            'memory_system': self.has_memory_system,
            'agent_loader': self.has_agent_loader,
            'skill_manager': self.has_skill_manager,
        }

    def log_pipeline_summary(self):
        """Log a summary of pipeline integration status"""
        print("\n" + "="*80)
        print("📊 PIPELINE INTEGRATION STATUS")
        print("="*80 + "\n")

        status = self.get_integration_status()

        print("Integrations:")
        for name, enabled in status.items():
            emoji = "✅" if enabled else "❌"
            print(f"   {emoji} {name}")

        if self.has_agent_loader:
            agents = self.get_available_agents()
            print(f"\n   Available Agents: {len(agents)}")

        if self.has_skill_manager:
            skills = self.get_available_skills()
            print(f"   Available Skills: {len(skills)}")

        print()


# Singleton instance
_pipeline_integration: Optional[PipelineIntegration] = None


def get_pipeline_integration(blackbox_root: Optional[Path] = None) -> PipelineIntegration:
    """
    Get the singleton PipelineIntegration instance.

    Args:
        blackbox_root: Path to blackbox root (uses cwd if None)

    Returns:
        PipelineIntegration instance
    """
    global _pipeline_integration

    if _pipeline_integration is None:
        root = blackbox_root or Path.cwd()
        _pipeline_integration = PipelineIntegration(root)

    return _pipeline_integration


def test_integration():
    """Test pipeline integration"""
    import tempfile
    import shutil

    # Create a temporary test environment
    test_dir = tempfile.mkdtemp(prefix="bb5_pipeline_test_")

    try:
        print(f"\n🧪 Testing Pipeline Integration")
        print(f"Test directory: {test_dir}\n")

        integration = PipelineIntegration(Path(test_dir))
        integration.log_pipeline_summary()

        # Test event publishing
        if integration.has_event_bus:
            print("📤 Testing event publishing...")
            integration.publish_pipeline_event(
                event_type="test",
                pipeline_type="feature",
                data={"test": "data"}
            )
            print("✅ Event published")

        # Test state persistence
        if integration.has_memory_system:
            print("\n💾 Testing state persistence...")
            integration.save_pipeline_state(
                pipeline_type="feature",
                run_id="test_001",
                state={"test": "state"}
            )
            loaded = integration.load_pipeline_state(
                pipeline_type="feature",
                run_id="test_001"
            )
            if loaded:
                print("✅ State persisted and loaded")
            else:
                print("❌ State load failed")

        print("\n✅ Integration test complete\n")

    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    test_integration()
