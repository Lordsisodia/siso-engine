# GitHub Issues Analysis: BMAD

**Repository:** bmad-code-org/BMAD-METHOD
**Generated:** 2026-01-19 08:28:49
**Focus Area:** bmad

## Summary

- **Total issues fetched:** 20
- **New issues analyzed:** 10
- **Previously seen:** 10

## Issue #1317: create-workflow produces non-compliant workflows (missing Universal Rules, Role format, etc.)

**State:** OPEN
**Created:** 2026-01-13T09:35:05Z
**URL:** https://github.com/bmad-code-org/BMAD-METHOD/issues/1317

### Description

# Issue Report: create-workflow produces non-compliant workflows

## Summary

Workflows created by the official `create-workflow` workflow do not fully comply with BMAD template standards (`workflow-template.md` and `step-template.md`). This was discovered during a `workflow-compliance-check` analys...

### Analysis

This issue relates to bmad. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #1314: There are two shard-docs.

**State:** OPEN
**Created:** 2026-01-12T17:11:22Z
**URL:** https://github.com/bmad-code-org/BMAD-METHOD/issues/1314

### Description

There are two shard-doc files, one in bmad-tool-core and the other in bmad-task-core. They are identical; is this a duplication?

### Analysis

This issue relates to bmad. Related to **documentation**. Impact assessment needed based on labels and community engagement.

## Issue #1308: Trae can not load bmad agent ,but copilot and  can success

**State:** OPEN
**Created:** 2026-01-11T13:50:38Z
**URL:** https://github.com/bmad-code-org/BMAD-METHOD/issues/1308

### Description

**Describe the bug**
我用vscode调用copilot和 cursor可以成功使用bmad 但是trae 都不行 无法使用bmad的agent

BMad Method version: version: 6.0.0-alpha.23


vscode结合copilot可以成功使用的截图<img width="2560" height="1379" alt="Image" src="https://github.com/user-attachments/assets/510c4a7d-91b9-4dc5-b3dd-b11df2a71a6c" />
cursor可以使用的截...

### Analysis

This issue relates to bmad. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #1301: [Bug] ERR_REQUIRE_ESM: inquirer cannot be required in install.js (v6.0.0-alpha.22)

**State:** OPEN
**Created:** 2026-01-10T20:53:02Z
**URL:** https://github.com/bmad-code-org/BMAD-METHOD/issues/1301

### Description

## Description
Running `npx bmad-method@alpha install` fails with ERR_REQUIRE_ESM error.

## Environment
- Node.js: v22.11.0
- npm: 11.7.0
- OS: macOS
- bmad-method version: 6.0.0-alpha.22

## Error
```
Error [ERR_REQUIRE_ESM]: require() of ES Module .../node_modules/inquirer/lib/index.js 
from .../...

### Analysis

This issue relates to bmad. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #1299: [BMB] Create-agent workflow outputs to bmb-creations with no install path to runtime location

**State:** OPEN
**Created:** 2026-01-10T19:15:15Z
**URL:** https://github.com/bmad-code-org/BMAD-METHOD/issues/1299

### Description

## Problem

The BMB create-agent workflow outputs a `.agent.yaml` file to `_bmad-output/bmb-creations/`, but there's no mechanism to install this agent to where Claude actually loads it.

## Current Flow (Broken)

```
1. User runs create-agent workflow
2. Workflow outputs: _bmad-output/bmb-creations...

### Analysis

This issue relates to bmad. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #1297: Step-04 of the bmb agent-builder references files that do not exist in workflows/agent/data/reference

**State:** OPEN
**Created:** 2026-01-10T17:14:14Z
**URL:** https://github.com/bmad-code-org/BMAD-METHOD/issues/1297

### Description

In lines 12 to 14 the file _bmad\bmb\workflows\agent\steps-c\step-04-persona.md references files like this : 

```
# Example Personas (for reference)
simpleExample: ../data/reference/simple-examples/commit-poet.agent.yaml
expertExample: ../data/reference/expert-examples/journal-keeper/journal-keeper...

### Analysis

This issue relates to bmad. Related to **documentation**. Impact assessment needed based on labels and community engagement.

## Issue #1294: Installer does not create custom module agents and throws an error

**State:** OPEN
**Created:** 2026-01-10T10:32:58Z
**URL:** https://github.com/bmad-code-org/BMAD-METHOD/issues/1294

### Description

Using bmb I created a custom module with 4 agents and 7 workflows. From what I can evaluate all required files are present and completed.

Used installer to add the custom module and got the following results:

1. For Claude and Gemini and Opencode:
Agents are *not* created.
Workflows are created co...

### Analysis

This issue relates to bmad. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #1293: 'build' argument at install is unknown

**State:** OPEN
**Created:** 2026-01-10T09:55:55Z
**URL:** https://github.com/bmad-code-org/BMAD-METHOD/issues/1293

### Description

Wanted to 'compile' a customized agent. Found instructions on how to 'Rebuild the Agent' in the docs here: https://docs.bmad-method.org/how-to/customization/customize-agents/.

It instructs to perform:
`npx bmad-method@alpha build <agent-name>`

Unfortunately the `build` argument throws this error:
...

### Analysis

This issue relates to bmad. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #1288: Custom module builder (bmb) does not create "code" field in module.yaml

**State:** OPEN
**Created:** 2026-01-09T16:56:35Z
**URL:** https://github.com/bmad-code-org/BMAD-METHOD/issues/1288

### Description

Created a new module using bmb. Then tried to install it using the custom module selection in the bmad installer. After the installer asks for the path to the module it returns this error message:

`>> module.yaml must contain a "code" field for the module ID`

Manually checking the module.yaml file...

### Analysis

This issue relates to bmad. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #1287: Epic Retrospective Workflow: Add Incremental Output and Upgrade to Step-Based Architecture

**State:** OPEN
**Created:** 2026-01-09T16:43:39Z
**URL:** https://github.com/bmad-code-org/BMAD-METHOD/issues/1287

### Description

# Epic Retrospective Workflow: Add Incremental Output and Upgrade to Step-Based Architecture

## Problem

The epic retrospective workflow (`src/modules/bmm/workflows/4-implementation/retrospective/`) currently only saves output at the very end of execution (Step 11: "Save Retrospective and Update Sp...

### Analysis

This issue relates to bmad. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Recommendations

- Review 10 new issues above
- Prioritize based on labels and community response
- Consider backlog items for high-priority patterns

