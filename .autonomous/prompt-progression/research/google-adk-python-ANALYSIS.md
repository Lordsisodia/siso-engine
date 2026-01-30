# GitHub Issues Analysis: Google ADK

**Repository:** google/adk-python
**Generated:** 2026-01-19 08:28:39
**Focus Area:** google-adk

## Summary

- **Total issues fetched:** 20
- **New issues analyzed:** 10
- **Previously seen:** 10

## Issue #4199: [Bug - Agent Analytics] Time to First Token vs Total Time

**State:** OPEN
**Created:** 2026-01-19T01:28:14Z
**URL:** https://github.com/google/adk-python/issues/4199

### Description

**Describe the bug**
I've noticed that in the BigQuery Agent Analytics Plugin, the time to first token vs the total time taken under the latency metrics is always exactly the same. This causes some discrepancies when implementing observability.

**To Reproduce**
1. Install the BigQuery Agent Analyti...

### Analysis

This issue relates to google-adk. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #4174: [BUG] LiteLLM (OpenAI/gpt-4o-mini): load_artifacts PDF attachment fails with “Invalid file data: 'file_id' … expected application/pdf, got None”

**State:** OPEN
**Created:** 2026-01-16T07:55:53Z
**URL:** https://github.com/google/adk-python/issues/4174

**Labels:** models

### Description

**Describe the bug**

When a user uploads a PDF and asks “what do you see in this PDF?”, ADK **SaveFilesAsArtifactsPlugin** saves the file as an artifact and adds an artifact placeholder. Then the agent calls the **load_artifacts tool** to inline/attach the artifact content. This flow works on Gemin...

### Analysis

This issue relates to google-adk. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #4173: Agent incorrectly invokes hallucinated tool  instead of proper validation

**State:** OPEN
**Created:** 2026-01-16T06:59:48Z
**URL:** https://github.com/google/adk-python/issues/4173

**Labels:** core

### Description

### **Describe the bug**
Agent incorrectly invokes hallucinated tool 'readLine' instead of proper validation. The LLM attempts to call a non-existent tool mentioned in the instruction, causing a ValueError crash instead of graceful handling.

### **To Reproduce**
Minimal code to reproduce:
```python...

### Analysis

This issue relates to google-adk. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #4172: [Bug] 500 Internal Server Error on /openapi.json: PydanticSchemaGenerationError for ClientSession

**State:** OPEN
**Created:** 2026-01-16T06:29:26Z
**URL:** https://github.com/google/adk-python/issues/4172

**Labels:** web

### Description

** Please make sure you read the contribution guide and file the issues in the right place. **
[Contribution guide.](https://google.github.io/adk-docs/contributing-guide/)

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Please share a minimal code and data...

### Analysis

This issue relates to google-adk. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #4169: wrong agent to start a new invocation when last invocation was rewound

**State:** OPEN
**Created:** 2026-01-15T18:59:45Z
**URL:** https://github.com/google/adk-python/issues/4169

**Labels:** core, request clarification

### Description

** Please make sure you read the contribution guide and file the issues in the right place. **
[Contribution guide.](https://google.github.io/adk-docs/contributing-guide/)

**Describe the bug**
When we use `rewind_async` to cancel an invocation, roll back the state changes, and start a new invocatio...

### Analysis

This issue relates to google-adk. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #4167: VertexAiMemoryBankService is not configured in Agent Engine

**State:** OPEN
**Created:** 2026-01-15T10:01:20Z
**URL:** https://github.com/google/adk-python/issues/4167

**Labels:** agent engine

### Description

**Describe the bug**
I want to use VertexAiMemoryBankService to store a use preference between agent runs.
My understanding is, upon deployement to agent engine is being used per default, but it is not

**To Reproduce**
1. define an simple agent with tools, which save and qury user preference from t...

### Analysis

This issue relates to google-adk. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #4166: OpenAPIToolset automatically converts camelCase to snake_case with no option to disable

**State:** OPEN
**Created:** 2026-01-15T09:54:03Z
**URL:** https://github.com/google/adk-python/issues/4166

**Labels:** tools

### Description

**Is your feature request related to a problem? Please describe.**
ADK's OpenAPIToolset automatically converts camelCase to snake_case when generating tool parameters, and there doesn't appear to be a built-in option to disable this. This is a problem when calling APIs which expect camelCase propert...

### Analysis

This issue relates to google-adk. Related to **documentation**. Impact assessment needed based on labels and community engagement.

## Issue #4164: ADK Session should have display_name and align with AgentEngine Sessions interface

**State:** OPEN
**Created:** 2026-01-15T04:55:56Z
**URL:** https://github.com/google/adk-python/issues/4164

**Labels:** agent engine

### Description

**Is your feature request related to a problem? Please describe.**
VertexAI AgentEngine Sessions supports properties which help in naming the session `displayName` and filtering `labels`. These are not present in ADK, making it hard to filter/name the session.

`DisplayName` is very basic as it serv...

### Analysis

This issue relates to google-adk. Related to **documentation**. Impact assessment needed based on labels and community engagement.

## Issue #4162: ADK doesn't report errors from McpToolset

**State:** OPEN
**Created:** 2026-01-14T23:00:32Z
**URL:** https://github.com/google/adk-python/issues/4162

**Labels:** tools, mcp

### Description

** Please make sure you read the contribution guide and file the issues in the right place. **
[Contribution guide.](https://google.github.io/adk-docs/contributing-guide/)

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Please share a minimal code and data...

### Analysis

This issue relates to google-adk. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #4159: ValueError: "No function call event found" for function responses in 1.22.1 with SequentialAgent and AgentTool

**State:** OPEN
**Created:** 2026-01-14T19:58:02Z
**URL:** https://github.com/google/adk-python/issues/4159

**Labels:** core

### Description

**Describe the bug**
`ValueError: No function call event found for function responses ids` occurs in `google-adk==1.22.1` when using a `SequentialAgent` wrapped in an `AgentTool`. This error signifies a mismatch/missing event in the conversation history, specifically when a sub-agent within the `Seq...

### Analysis

This issue relates to google-adk. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Recommendations

- Review 10 new issues above
- Prioritize based on labels and community response
- Consider backlog items for high-priority patterns

