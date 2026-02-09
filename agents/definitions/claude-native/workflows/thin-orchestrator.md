# Thin Orchestrator Pattern for BlackBox5

**Location:** `2-engine/agents/definitions/claude-native/workflows/thin-orchestrator.md`

**Based on:** GSD (Get-Shit-Done) Framework by @glittercowboy

---

## Overview

The Thin Orchestrator pattern is a fundamental shift from traditional orchestration:

| Aspect | Heavy Orchestrator | Thin Orchestrator |
|--------|-------------------|-------------------|
| **Context Usage** | Accumulates work (80%+) | Stays lean (30-40%) |
| **Work Location** | Orchestrator does tasks | Sub-agents do tasks |
| **Context Quality** | Degrades over time | Fresh per sub-agent |
| **Parallelism** | Limited | Maximum |

**Core Principle:**
> "The orchestrator never does heavy lifting. It spawns agents, waits, integrates results."

---

## Context Budget

```
Total Available: 200k tokens per agent

Thin Orchestrator:     ~15%  (30k tokens)
  - Coordination logic
  - State tracking
  - Result integration
  - Routing decisions

Each Sub-Agent:       100%  (200k tokens)
  - Fresh context
  - Zero accumulated garbage
  - Full capacity for task
```

**Result:** Task 50 has the same quality as Task 1.

---

## The 4 Stages

### Stage 1: Research

**Orchestrator Does:**
- Spawns 4 parallel researchers
- Waits for completion
- Triggers synthesis

**Sub-Agents Do:**
- Deep research with fresh context
- Write structured findings
- Return brief confirmation

### Stage 2: Planning

**Orchestrator Does:**
- Spawns Planner + Checker loop
- Manages iteration (max 3)
- Approves final plan

**Sub-Agents Do:**
- Planner: Creates XML task structure
- Checker: Validates against 7 dimensions

### Stage 3: Execution

**Orchestrator Does:**
- Parses dependencies
- Groups into waves
- Spawns executors
- Tracks progress

**Sub-Agents Do:**
- Each executor gets fresh context
- Implements assigned tasks
- Returns brief status

### Stage 4: Verification

**Orchestrator Does:**
- Spawns Verifier
- If fails, spawns Debugger
- Routes to fix or complete

**Sub-Agents Do:**
- Verifier: 3-level artifact check
- Debugger: Root cause analysis

---

## Orchestrator Responsibilities

### What It DOES Do

1. **Discover** - Find plans, parse dependencies
2. **Analyze** - Group into waves, detect cycles
3. **Spawn** - Launch sub-agents with fresh context
4. **Wait** - Block until sub-agents complete
5. **Integrate** - Combine results, update state
6. **Route** - Decide next stage based on results
7. **Track** - Monitor progress, handle failures

### What It DOESN'T Do

| Don't Do | Delegate To |
|----------|-------------|
| Read source files | Researcher agents |
| Write code | Executor agents |
| Run tests | Verifier agents |
| Deep analysis | Specialist agents |
| Debug failures | Debugger agents |
| Make implementation decisions | Planner agents |

---

## Implementation Pattern

```python
class ThinOrchestrator:
    """Thin orchestrator that coordinates but never does heavy lifting."""

    async def execute_phase(self, phase_config):
        # Stage 1: Research (4 parallel agents)
        research = await self._run_research(phase_config)

        # Stage 2: Planning (Planner+Checker loop)
        plan = await self._run_planning(research)

        # Stage 3: Execution (Wave-based)
        execution = await self._run_execution(plan)

        # Stage 4: Verification
        return await self._run_verification(execution)

    async def _run_research(self, config):
        """Spawn 4 parallel researchers."""
        researchers = [
            Task(prompt="Research stack", subagent_type="bb5-stack-researcher"),
            Task(prompt="Research arch", subagent_type="bb5-architecture-researcher"),
            Task(prompt="Research conventions", subagent_type="bb5-convention-researcher"),
            Task(prompt="Research risks", subagent_type="bb5-risk-researcher"),
        ]
        return await asyncio.gather(*researchers)

    async def _run_planning(self, research):
        """Run Planner+Checker loop."""
        for i in range(3):  # Max 3 iterations
            plan = await Task(prompt="Create plan", subagent_type="bb5-planner")
            check = await Task(prompt="Check plan", subagent_type="bb5-checker")
            if check.status == "PASS":
                return plan
        raise PlanningFailed("Max iterations reached")

    async def _run_execution(self, plan):
        """Execute in waves."""
        waves = self._calculate_waves(plan)
        for wave_num, wave in enumerate(waves):
            results = await asyncio.gather(*[
                Task(prompt=task, subagent_type="bb5-executor")
                for task in wave
            ])
        return results

    async def _run_verification(self, execution):
        """Verify + debug if needed."""
        verify = await Task(prompt="Verify", subagent_type="bb5-verifier")
        if verify.status == "FAIL":
            debug = await Task(prompt="Debug", subagent_type="bb5-debugger")
        return verify
```

---

## Benefits

| Metric | Heavy Orchestrator | Thin Orchestrator |
|--------|-------------------|-------------------|
| Session Length | 2-3 hours | 8+ hours |
| Task 50 Quality | Degraded | Same as Task 1 |
| Parallelism | Limited | Maximum |
| Context Rot | Yes | No |
| Recovery from Failure | Hard | Easy |

---

## References

- [GSD Framework](https://github.com/glittercowboy/get-shit-done)
- [Wave Execution](./wave-execution.md)
- [Planner+Checker Loop](./planner-checker-loop.md)
