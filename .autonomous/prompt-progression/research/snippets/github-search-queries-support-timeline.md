# GitHub Search Queries — Support timeline + inbox primitives (v2, higher precision)

Goal: find OSS we can reuse for:
support timeline primitives (threads, messages, assignments, internal notes),
shared inbox / ticketing primitives (queues, states, tagging, SLAs),
and embeddable chat widget patterns (loader + identity handoff) as reference implementations.

This query bank is intentionally **not** “find an entire helpdesk platform”.
We prefer **embeddable primitives** and “implementation-shaped” repos.

Recommended run settings:
Use `--no-derived-queries`. Keep `--min-stars` around `30–50` (many high-signal support primitives are niche).
Use strong excludes for AI/LLM + note-taking apps + spammy “chat apps”.

---

## Core support primitives (inbox/ticketing)

Topic signals (expands into `topic:<token>` queries automatically):
- `helpdesk`, `ticketing`, `shared-inbox`, `customer-support`, `customer-service`, `support`, `livechat`, `chat-widget`

Keyword queries (wider match; avoid “open source” requiring exact phrasing):
- `open source helpdesk`
- `open source ticketing system`
- `shared inbox open source`
- `customer support inbox`
- `django helpdesk`
- `laravel helpdesk`
- `helpdesk ticket assignment`
- `helpdesk sla`
- `ticket queue assignment`

## Timeline / activity feed UI (support-adjacent)

- `conversation timeline ui component react`
- `activity feed ui component react`
- `event timeline ui component react`
- `customer timeline ui component`

## Embeddable chat widget patterns (boot + identity)

- `embeddable chat widget react`
- `chat widget loader snippet`
- `website chat widget typescript`
- `customer support chat widget`

## Integration primitives (APIs / adapters)

- `zendesk api client`
- `intercom api client`
- `helpscout api client`
- `helpdesk webhook integration`

---

## Exclusion guidance (reduce churn)

Prefer running with:
`--exclude-keywords "ai,llm,chatgpt,copilot,knowledge-base,notes,note-taking,wiki,pkm"`
and
`--exclude-regex "\\b(ai|llm|chatgpt|copilot|knowledge\\s*base|notes?|note-taking|pkm|second\\s*brain|obsidian|notion)\\b"`.

Rationale: support primitives are frequently polluted by LLM apps and PKM/note products; we want threads/messages/assignment patterns, not “chatbot UI”.
