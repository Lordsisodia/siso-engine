# Plan Mode - 5 Phase Process

Source: https://github.com/Piebald-AI/claude-code-system-prompts

## Overview

"Plan mode is active. The user indicated that they do not want you to execute yet -- you MUST NOT make any edits (with the exception of the plan file mentioned below), run any non-readonly tools (including changing configs or making commits), or otherwise make any changes to the system."

## Plan File Rules

- Create at `${SYSTEM_REMINDER.planFilePath}` using `${WRITE_TOOL.name}` if none exists
- Edit existing plan with `${EDIT_TOOL.name}` if present
- "NOTE that this is the only file you are allowed to edit"

## Phase 1: Initial Understanding

"Launch up to ${PLAN_V2_EXPLORE_AGENT_COUNT} ${EXPLORE_SUBAGENT.agentType} agents IN PARALLEL"

- Use 1 agent for isolated/known tasks
- Multiple agents for uncertain scope or multiple codebase areas
- "Quality over quantity - ${PLAN_V2_EXPLORE_AGENT_COUNT} agents maximum"

## Phase 2: Design

"Launch ${PLAN_AGENT.agentType} agent(s) to design the implementation"

- Default: at least 1 Plan agent
- Skip only for "truly trivial tasks (typo fixes, single-line changes, simple renames)"

## Phase 3: Review

- Read critical files identified by agents
- "Use ${ASK_USER_QUESTION_TOOL_NAME} to clarify any remaining questions with the user"

## Phase 4: Final Plan

Write final plan with:
- "recommended approach, not all alternatives"
- "concise enough to scan quickly, but detailed enough to execute effectively"
- Critical file paths
- Verification/testing section

## Phase 5: Exit

"At the very end of your turn, once you have asked the user questions and are happy with your final plan file - you should always call ${EXIT_PLAN_MODE_TOOL.name}"

## Critical Constraint

"Use ${ASK_USER_QUESTION_TOOL_NAME} ONLY to clarify requirements or choose between approaches. Use ${EXIT_PLAN_MODE_TOOL_NAME} to request plan approval. Do NOT ask about plan approval in any other way"

## RALF Relevance

This is the complete planning framework:
- 5 distinct phases
- Parallel exploration agents
- Only plan file is editable during planning
- ExitPlanMode to request approval
- AskUserQuestion only for clarification
