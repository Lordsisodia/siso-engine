"""
BlackBox5 Main Entry Point

Provides the primary interface for accessing the BlackBox5 system.
This module initializes and manages core components including agents,
skill managers, and guide registries.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Singleton instance
_blackbox5_instance: Optional['BlackBox5'] = None


class BlackBox5:
    """
    Main BlackBox5 system interface.
    
    Provides access to:
    - Agent management
    - Skill management
    - Guide registry
    - Request processing
    """
    
    def __init__(self):
        """Initialize the BlackBox5 system."""
        self._agents: Dict[str, Any] = {}
        self._skill_manager: Optional[Any] = None
        self._guide_registry: Optional[Any] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize all system components."""
        if self._initialized:
            return
            
        logger.info("Initializing BlackBox5 system...")
        
        # Initialize agent loader and load agents
        try:
            from agents.framework.agent_loader import AgentLoader
            agent_loader = AgentLoader()
            loaded_agents = await agent_loader.load_all()
            self._agents = loaded_agents
            logger.info(f"Loaded {len(self._agents)} agents")
        except Exception as e:
            logger.warning(f"Could not load agents: {e}")
            self._agents = {}
        
        # Initialize skill manager
        try:
            from agents.framework.skill_manager import SkillManager
            self._skill_manager = SkillManager()
            logger.info("Skill manager initialized")
        except Exception as e:
            logger.warning(f"Could not initialize skill manager: {e}")
            self._skill_manager = None
        
        # Initialize guide registry (placeholder - implement as needed)
        self._guide_registry = None
        
        self._initialized = True
        logger.info("BlackBox5 system initialized")
    
    async def process_request(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user request.
        
        Args:
            query: The user's query or task
            session_id: Optional session ID for continuity
            context: Optional context dictionary
            
        Returns:
            Dictionary containing the result and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        context = context or {}
        
        # Determine execution strategy
        strategy = context.get('strategy', 'auto')
        forced_agent = context.get('forced_agent')
        
        # Simple routing logic
        if forced_agent and forced_agent in self._agents:
            agent = self._agents[forced_agent]
            routing = {
                'strategy': 'single_agent',
                'agent': forced_agent,
                'complexity': 0.5,
                'confidence': 0.9
            }
        elif len(self._agents) > 0:
            # Use first available agent as default
            agent_name = list(self._agents.keys())[0]
            agent = self._agents[agent_name]
            routing = {
                'strategy': strategy if strategy != 'auto' else 'single_agent',
                'agent': agent_name,
                'complexity': 0.5,
                'confidence': 0.8
            }
        else:
            # No agents available
            return {
                'success': False,
                'error': 'No agents available',
                'routing': {'strategy': 'none', 'agent': None},
                'session_id': session_id,
                'timestamp': str(asyncio.get_event_loop().time())
            }
        
        # Process the request (simplified)
        try:
            # Create a simple result structure
            result = {
                'success': True,
                'output': f"Processed: {query}",
                'error': None,
                'metadata': {
                    'agent_used': routing['agent'],
                    'strategy': routing['strategy']
                }
            }
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            result = {
                'success': False,
                'output': '',
                'error': str(e),
                'metadata': {}
            }
        
        return {
            'result': result,
            'routing': routing,
            'session_id': session_id or 'default',
            'timestamp': str(asyncio.get_event_loop().time()),
            'guide_suggestions': []
        }


async def get_blackbox5() -> BlackBox5:
    """
    Get the singleton BlackBox5 instance.
    
    Returns:
        Initialized BlackBox5 instance
    """
    global _blackbox5_instance
    
    if _blackbox5_instance is None:
        _blackbox5_instance = BlackBox5()
        await _blackbox5_instance.initialize()
    
    return _blackbox5_instance
