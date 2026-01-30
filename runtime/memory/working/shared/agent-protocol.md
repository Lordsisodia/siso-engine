# BLACKBOX4 AGENT PROTOCOL

You are part of the Blackbox4 autonomous task management system.

## MANDATORY BEHAVIOR

You MUST follow the agent behavior protocol at:
`.blackbox/.docs/1-getting-started/AGENT-BEHAVIOR-PROTOCOL.md`

## STARTUP CHECKLIST

On startup, you MUST:

1. Read the protocol file
2. Load: `.blackbox/.memory/working/shared/work-queue.json`
3. Read: `.blackbox/.memory/working/shared/timeline.md`
4. Write your startup entry to timeline.md
5. Update task status to "in_progress"
6. Begin execution

## TIMELINE LOGGING

You MUST write to timeline.md:
- When you START work
- Every 5-10 minutes of PROGRESS
- When you COMPLETE work
- When you ERROR
- When you HANDOFF to another agent

## CONTEXT PRESERVATION

Before shutdown or handoff, you MUST:
1. Save all conversation history
2. Document all decisions made
3. List all artifacts created
4. Specify next steps
5. Save to: `.blackbox/.memory/working/shared/task-context/[task_id].json`

## WORK QUEUE UPDATES

You MUST update work-queue.json when:
- Starting a task
- Completing a task
- Changing status
- Encountering blockers
- Making decisions

## NON-NEGOTIABLE

- Log ALL actions to timeline.md
- Update work-queue.json on status changes
- Save context before shutdown
- Follow handoff protocol for task transfers

---
**END OF PROTOCOL**
