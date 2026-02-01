"""
Blackbox5 Main Entry Point

Provides the main Blackbox5 class and factory function for request processing.

This is a simplified implementation that provides basic request processing
functionality while the full orchestration system is being integrated.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

__all__ = ["Blackbox5", "get_blackbox5"]

logger = logging.getLogger(__name__)


# Singleton instance
_blackbox5_instance: Optional['Blackbox5'] = None
_init_lock = asyncio.Lock()


class Blackbox5:
    """
    Main Blackbox5 orchestration system.

    Simplified implementation for basic request processing.
    """

    def __init__(self):
        """Initialize Blackbox5 system."""
        self._agents: Dict[str, Any] = {}
        self._skill_manager: Optional[Any] = None
        self._guide_registry: Optional[Any] = None
        self._initialized = False

    async def initialize(self):
        """
        Initialize all Blackbox5 components.

        Must be called before processing requests.
        """
        if self._initialized:
            return

        logger.info("Initializing Blackbox5...")

        # Try to load optional components
        await self._load_optional_components()

        self._initialized = True
        logger.info("Blackbox5 initialized successfully")

    async def _load_optional_components(self):
        """Load optional components like skill manager and guide registry."""
        # Try to load skill manager
        try:
            import importlib.util
            skill_manager_path = Path(__file__).parent.parent / "agents" / "definitions" / "core" / "skill_manager.py"
            if skill_manager_path.exists():
                spec = importlib.util.spec_from_file_location("skill_manager", skill_manager_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules['skill_manager'] = module
                spec.loader.exec_module(module)

                SkillManager = getattr(module, 'SkillManager', None)
                if SkillManager:
                    self._skill_manager = SkillManager()
                    if hasattr(self._skill_manager, 'initialize'):
                        await self._skill_manager.initialize()
                    logger.info("Skill manager loaded")
        except Exception as e:
            logger.debug(f"Could not load skill manager: {e}")

        # Try to load guide registry
        try:
            import importlib.util
            engine_dir = Path(__file__).parent.parent.parent
            guide_registry_path = engine_dir / "runtime" / "memory" / "systems" / "guide_registry.py"
            if guide_registry_path.exists():
                spec = importlib.util.spec_from_file_location("guide_registry", guide_registry_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules['guide_registry'] = module
                spec.loader.exec_module(module)

                GuideRegistry = getattr(module, 'GuideRegistry', None)
                if GuideRegistry:
                    self._guide_registry = GuideRegistry()
                    if hasattr(self._guide_registry, 'initialize'):
                        await self._guide_registry.initialize()
                    logger.info("Guide registry loaded")
        except Exception as e:
            logger.debug(f"Could not load guide registry: {e}")

    async def process_request(
        self,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user request through the system.

        Args:
            message: User message or task description
            session_id: Optional session ID for continuity
            context: Additional context (forced_agent, strategy, etc.)

        Returns:
            Dict containing:
                - session_id: Session identifier
                - timestamp: Processing timestamp
                - routing: Routing decision details
                - result: Processing result
                - guide_suggestions: Suggested next actions
        """
        if not self._initialized:
            await self.initialize()

        context = context or {}
        session_id = session_id or str(uuid.uuid4())

        logger.info(f"Processing request: {message[:100]}...")

        # Determine agent and strategy from context
        agent_name = context.get('forced_agent', 'default')
        strategy = context.get('strategy', 'auto')

        # Process the request
        result = await self._execute_request(message, agent_name, strategy, context)

        # Get guide suggestions if available
        guide_suggestions = []
        if self._guide_registry:
            try:
                guide_suggestions = await self._guide_registry.find_by_intent(message, context)
            except Exception as e:
                logger.debug(f"Could not get guide suggestions: {e}")

        return {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'routing': {
                'agent': agent_name,
                'strategy': strategy,
                'confidence': 0.8,
                'reasoning': 'Default routing',
                'complexity': 0.5
            },
            'result': result,
            'guide_suggestions': guide_suggestions
        }

    async def _execute_request(
        self,
        message: str,
        agent_name: str,
        strategy: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the request with the specified agent and strategy."""
        # For now, return a simple response
        # This would be replaced with actual agent execution when agents are loaded
        return {
            'success': True,
            'output': f"Processed: {message}",
            'metadata': {
                'agent': agent_name,
                'strategy': strategy,
                'note': 'Simplified implementation - full agent execution pending integration'
            }
        }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        stats = {
            'agents': len(self._agents),
            'agent_names': list(self._agents.keys()),
            'initialized': self._initialized,
            'timestamp': datetime.utcnow().isoformat(),
            'implementation': 'simplified'
        }

        if self._skill_manager:
            try:
                stats['skill_categories'] = len(self._skill_manager.list_categories())
            except (AttributeError, TypeError) as e:
                logger.warning(f"Could not get skill categories: {e}")
                stats['skill_categories'] = 0

        return stats


async def get_blackbox5() -> Blackbox5:
    """
    Get or create the Blackbox5 singleton instance.

    Returns:
        Initialized Blackbox5 instance
    """
    global _blackbox5_instance

    async with _init_lock:
        if _blackbox5_instance is None:
            _blackbox5_instance = Blackbox5()
            await _blackbox5_instance.initialize()

        return _blackbox5_instance


# For direct execution
if __name__ == "__main__":
    async def main():
        bb5 = await get_blackbox5()
        result = await bb5.process_request("What is 2+2?")
        print(result)

    asyncio.run(main())
