# Agent Framework

Core framework for BB5 agent system including base classes, loaders, and coordination.

## Files

| File | Purpose |
|------|---------|
| `base_agent.py` | Base agent class with common functionality |
| `agent_loader.py` | Loads and initializes all agents |
| `agent_coordinator.py` | Coordinates multi-agent workflows |
| `agent_factory.py` | Creates agent instances |

## BaseAgent

Abstract base class for all BB5 agents:

```python
from agents.framework.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="my_agent")

    async def execute(self, task):
        # Implementation
        return result
```

## AgentLoader

Loads all available agents from definitions:

```python
from agents.framework.agent_loader import AgentLoader

loader = AgentLoader()
agents = await loader.load_all()
```

## AgentCoordinator

Coordinates multiple agents in workflows:

```python
from agents.framework.agent_coordinator import AgentCoordinator

coordinator = AgentCoordinator()
result = await coordinator.execute_workflow(
    agents=["analyst", "architect", "developer"],
    task="Build feature"
)
```

## Related

- [Agent Definitions](../definitions/) - Agent implementations
- [Core Helpers](../../helpers/core/) - Base tool classes
