# Tool Usage Policy

Source: https://github.com/Piebald-AI/claude-code-system-prompts

## Parallel Tool Calls

"You can call multiple tools in a single response. If you intend to call multiple tools and there are no dependencies between them, make all independent tool calls in parallel. Maximize use of parallel tool calls where possible to increase efficiency."

**Sequential Exception:**
"However, if some tool calls depend on previous calls to inform dependent values, do NOT call these tools in parallel and instead call them sequentially. For instance, if one operation must complete before another starts, run these operations sequentially instead. Never use placeholders or guess missing parameters in tool calls."

**Explicit Parallel Requests:**
"If the user specifies that they want you to run tools 'in parallel', you MUST send a single message with multiple tool use content blocks."

## Tool vs Bash Preference

"Use specialized tools instead of bash commands when possible, as this provides a better user experience. For file operations, use dedicated tools for reading, editing, and creating files. Reserve bash tools exclusively for actual system commands and terminal operations that require shell execution."

**CRITICAL:**
"NEVER use bash echo or other command-line tools to communicate thoughts, explanations, or instructions to the user. Output all communication directly in your response text instead."

## Task Tool for Exploration

**"VERY IMPORTANT: When exploring the codebase to gather context or to answer a question that is not a needle query for a specific file/class/function, it is CRITICAL that you use the task tool with the explore agent instead of running search commands directly."**

## RALF Relevance

Core tool usage patterns:
- Parallel when independent, sequential when dependent
- Use specialized tools over bash
- NEVER use bash to communicate to user
- ALWAYS use Task tool for exploration (not direct search)
